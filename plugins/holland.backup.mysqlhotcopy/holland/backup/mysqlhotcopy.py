"""
Plugin for the Holland backup framework
to backup MySQL databases using mysqldump
"""

import os
import glob
import subprocess
import tempfile
import shutil
import logging

from holland.lib.mysql.client import connect, PassiveMySQLClient
from holland.lib.mysql.schema import MySQLSchema, \
                                     DatabaseIterator, \
                                     TableIterator
from holland.lib.mysql.option import make_mycnf
from holland.lib.archive import create_archive
from holland.core.util.path import format_bytes, disk_free
from holland.core.config.configobj import ConfigObj, ParseError
from holland.core.exceptions import BackupError

LOG = logging.getLogger(__name__)

# We validate our config against the following spec
CONFIGSPEC = """# MySQL Hotcopy Plugin Configuration
# This plugin backs up raw data files of non-transactional engines
# It's not so much "hot" as "warm" - tables should be locked during
# backup for consistency.
# This plugin also backs up .frm files for all table types

[mysqlhotcopy]
# Directories where mysql commands can be found
mysql-binpath       = string(default=None)
# How should tables be locked?
# flush-lock: global read lock (FLUSH TABLES WITH READ LOCK)
# lock-tables: lock only the tables being backed up
# default lock-tables. Use flush-lock if bin-log-position is set
lock-method         = option('flush-lock', 'lock-tables', 'none', default='lock-tables')
# Names of databases to backup
databases           = coerced_list(default=list('*'))
# Names of databases to exclude
exclude-databases   = coerced_list(default=list())
# Names of tables to backup
tables              = coerced_list(default=list('*'))
# Names of tables to exclude
exclude-tables      = coerced_list(default=list())
# Only backup the 2K header of MyISAM indexes
# (makes for faster backups sometimes, table must be repaired on restore)
partial-indexes     = boolean(default=false)
# How should tables be archived?
# dir - into a directory
# tar - into a tar archive
# zip - into a zip archive
# dir or zip offer constant time lookup and provides faster per-table restores
# tar probably gets somewhat better overall compression
archive-method      = option(dir,tar,zip,default="dir")
# stop the slave before running backups
stop-slave          = boolean(default=false)
# record the binary log position
bin-log-position    = boolean(default=false)

# Compression method
# Only applicable to certain archive types
# (e.g. zip only supports 'zlib' internal compression)
[compression]
method              = option('none','gzip','pigz','bzip2','lzma','lzop',default='gzip')
inline              = boolean(default=false)
level               = integer(default=1,min=0,max=9)
bin-path            = string(default=None)

# MySQL connection information
[mysql:client]
default-extra-files = coerced_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(default=None)
""".splitlines()

# Used for our surrogate connection
CLIENT_TIMEOUT = 28800

class MySQLHotcopy(object):
    """
    Plugin for backing up MySQL MyISAM tables
    """
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        if dry_run:
            LOG.info("Dry-run mode")
        self.dry_run = dry_run
        self.config.validate_config(CONFIGSPEC)
        # Setup MySQL connection objects
        mycnf_cfg = self.config['mysql:client']
        self.mycnf = build_mysql_config(mycnf_cfg)
        self.mycnf.filename = os.path.join(self.target_directory, 'my.cnf')
        self.mysqlclient = holland.lib.mysql.connect(self.mycnf)

    def estimate_backup_size(self):
        total = 0
        datadir = self.mysqlclient.show_variable('datadir')
        for cpath in self._find_files(datadir):
            st = os.stat(cpath)
            if cpath.endswith('.MYI') and self.config.lookup('mysqlhotcopy.partial-indexes'):
                total += min(st.st_size, 2048)
            else:
                total += st.st_size
        return total

    def backup(self):
        """
        Start a backup.  This attempts one or more mysqldump
        runs.  On error, a BackupError exception will be thrown.
        """

        if self.config.lookup('mysqlhotcopy.stop-slave'):
            self.mysqlclient.stop_slave()

        if self.config.lookup('mysqlhotcopy.bin-log-position'):
            #ensure mysql:replication section exists
            self.config.setdefault('mysql:replication', {})
            # Log slave data if we can:
            is_slave = self.mysqlclient.is_slave_running()
            if is_slave:
                slave_status = self.mysqlclient.show_slave_status()
                self.config['mysql:replication']['slave_master_log_file'] = slave_status['Relay_Master_Log_File']
                self.config['mysql:replication']['slave_master_log_pos'] = slave_status['Exec_Master_Log_Pos']
            master_data = self.mysqlclient.show_master_status()
            if not master_data and not is_slave:
                LOG.error("bin-log-position requested, but this server is neither a master nor a slave")
                raise BackupError("Failboat: replication not configured")
            self.config['mysql:replication']['master_log_file'] = master_data[0]
            self.config['mysql:replication']['master_log_pos'] = master_data[1]
            LOG.info("Writing master status to %s", self.mycnf.path)
            if not self.dry_run:
                self.config.write()

        # trap exceptions so we make sure to restart the slave, if we stopped it
        # if the slave was already stopped, we will raise an exception when we
        # try to stop it (above)
        error = None
        try:
            self._backup()
        except Exception, e:
            error = e

        if self.config.lookup('mysqlhotcopy.stop-slave'):
            self.mysqlclient.start_slave()

        if error:
            raise e

    def _backup(self):
        datadir = self.mysqlclient.show_variable('datadir')
        archive_method = self.config.lookup('mysqlhotcopy.archive-method')
        if not self.dry_run:
            archive = create_archive(archive_method, os.path.join(self.target_directory, 'backup_data'))
        LOG.info("Creating backup_data %s archive", archive_method)

        if self.config.lookup('mysqlhotcopy.lock-method') == 'flush-lock':
            if not self.dry_run:
                self.mysqlclient.flush_tables_with_read_lock(extra_flush=True)
        elif self.config.lookup('mysqlhotcopy.lock-method') == 'lock-tables':
            tables = [x for x in self._find_tables() if x not in [('mysql', 'general_log'), ('mysql', 'slow_log')]]
            quoted_tables = map(lambda x: '`' + '`.`'.join(x) +
                                '`', tables)
            if not self.dry_run:
                self.mysqlclient.lock_tables(quoted_tables)
                self.mysqlclient.flush_tables()

        LOG.info("Starting Backup")
        error = None
        try:
            if self.config.lookup('mysqlhotcopy.partial-indexes'):
                LOG.info("Only archiving partial indexes")
            for cpath in self._find_files(datadir):
                rpath = os.sep.join(cpath.split(os.sep)[-2:])
                if self.config.lookup('mysqlhotcopy.partial-indexes') \
                    and rpath.endswith('.MYI'):
                    if not self.dry_run:
                        partial_data = open(cpath, 'r').read(2048)
                        archive.add_string(partial_data, rpath)
                    LOG.debug("%s [partial]", rpath)
                else:
                    LOG.debug("%s", rpath)
                    if not self.dry_run:
                        archive.add_file(cpath, rpath)
        except Exception, e:
            error = e
            LOG.error("Failed to archive data file. %s", e)

        if not self.dry_run:
            self.mysqlclient.unlock_tables()
            archive.close()
        if error:
            raise e

    def cleanup(self):
        """
        Finish a backup.
        """
        pass

    def _find_files(self, datadir):
        for db, tbl in self._find_tables():
            base_path = os.path.join(datadir, db, tbl)
            if not os.path.exists(base_path + '.frm'):
                LOG.debug("ARGH %s does not exist", base_path + '.frm')
                if self.mysqlclient.server_version > (5, 1, 0):
                    LOG.debug("Checking for weird encoding...")
                    db = self.mysqlclient.encode_as_filename(db)
                    tbl = self.mysqlclient.encode_as_filename(tbl)
                    LOG.debug("Encoded db: %r", db)
                    LOG.debug("Encoded tbl: %r", tbl)
                base_path = os.path.join(datadir, db, tbl)
                if os.path.exists(base_path + '.frm'):
                    LOG.debug("Encoded path %s DOES exist", base_path)
                else:
                    LOG.debug("FAIL: encodes path %s also does not exist", base_path)
            # Escape any accidental glob patterns
            for c in ('[', ']', '*', '?'):
                base_path = base_path.replace(c, '\\' + c)
            for name in glob.glob(base_path + '.*'):
                yield name


provider = MySQLHotcopy
