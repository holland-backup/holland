"""Command Line Interface"""

import os
import re
import logging
from holland.core.exceptions import BackupError
from holland.lib.compression import open_stream
from holland.lib.mysql import MySQLSchema, connect, MySQLError
from holland.lib.mysql import include_glob, exclude_glob
from holland.lib.mysql import DatabaseIterator, MetadataTableIterator, \
                              SimpleTableIterator
from holland.backup.mysqldump.base import start
from holland.backup.mysqldump.util import INIConfig, update_config
from holland.backup.mysqldump.util.ini import OptionLine, CommentLine
from holland.lib.mysql.option import load_options, \
                                     write_options, \
                                     build_mysql_config
from holland.backup.mysqldump.command import MySQLDump, MySQLDumpError, \
                                             MyOptionError
from holland.backup.mysqldump.mock import MockEnvironment

LOG = logging.getLogger(__name__)

# We validate our config against the following spec
CONFIGSPEC = """
[mysqldump]
extra-defaults      = boolean(default=no)
mysql-binpath       = force_list(default=list())

lock-method         = option('flush-lock', 'lock-tables', 'single-transaction', 'auto-detect', 'none', default='auto-detect')

databases           = force_list(default=list('*'))
exclude-databases   = force_list(default=list())

tables              = force_list(default=list("*"))
exclude-tables      = force_list(default=list())

engines             = force_list(default=list("*"))
exclude-engines     = force_list(default=list())

flush-logs           = boolean(default=no)
flush-privileges    = boolean(default=no)
dump-routines       = boolean(default=no)
dump-events         = boolean(default=no)
stop-slave          = boolean(default=no)
bin-log-position    = boolean(default=no)

file-per-database   = boolean(default=yes)

additional-options  = force_list(default=list())

estimate-method = string(default='plugin')

[compression]
method        = option('none', 'gzip', 'pigz', 'bzip2', 'lzma', 'lzop', default='gzip')
inline              = boolean(default=yes)
level               = integer(min=0, max=9, default=1)

[mysql:client]
defaults-extra-file = force_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(min=0, default=None)
""".splitlines()

class MySQLDumpPlugin(object):
    """MySQLDump Backup Plugin interface for Holland"""
    CONFIGSPEC = CONFIGSPEC

    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.config.validate_config(self.CONFIGSPEC) # -> ValidationError

        # Setup a discovery shell to find schema items
        # This will iterate over items during the estimate
        # or backup phase, which will call schema.refresh()
        self.schema = MySQLSchema()
        config = self.config['mysqldump']
        self.schema.add_database_filter(include_glob(*config['databases']))
        self.schema.add_database_filter(
                exclude_glob(*config['exclude-databases'])
        )
        self.schema.add_table_filter(include_glob(*config['tables']))
        self.schema.add_table_filter(exclude_glob(*config['exclude-tables']))
        self.schema.add_engine_filter(include_glob(*config['engines']))
        self.schema.add_engine_filter(exclude_glob(*config['exclude-engines']))

        self.mysql_config = build_mysql_config(self.config['mysql:client'])
        self.client = connect(self.mysql_config['client'])

    def estimate_backup_size(self):
        """Estimate the size of the backup this plugin will generate"""
        LOG.info("Estimating size of mysqldump backup")
        estimate_method = self.config['mysqldump']['estimate-method']

        if estimate_method.startswith('const:'):
            try:
                return parse_size(estimate_method[6:])
            except ValueError, exc:
                raise BackupError(str(exc))

        if estimate_method != 'plugin':
            raise BackupError("Invalid estimate-method '%s'" % estimate_method)

        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = MetadataTableIterator(self.client)
            try:
                self.client.connect()
                self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            except MySQLError, exc:
                raise BackupError("MySQL Error [%d] %s" % exc.args)
            return sum([db.size for db in self.schema.databases])
        finally:
            self.client.disconnect()

    def _fast_refresh_schema(self):
        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = SimpleTableIterator(self.client, record_engines=True)
            try:
                self.client.connect()
                self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            except MySQLError, exc:
                raise BackupError("MySQL Error [%d] %s" % exc.args)
        finally:
            self.client.disconnect()

    def backup(self):
        """Run a MySQL backup"""

        if self.schema.timestamp is None:
            self._fast_refresh_schema()

        mock_env = None
        if self.dry_run:
            mock_env = MockEnvironment()
            mock_env.replace_environment()
            LOG.info("Running in dry-run mode.")

        try:
            self._backup()
        finally:
            if mock_env:
                mock_env.restore_environment()

    def _backup(self):
        """Real backup method.  May raise BackupError exceptions"""
        if self.config['mysqldump']['stop-slave']:
            self.config.setdefault('mysql:replication', {})
            _stop_slave(self.client, self.config['mysql:replication'])

        config = self.config['mysqldump']

        # setup defaults_file with ignore-table exclusions
        defaults_file = os.path.join(self.target_directory, 'my.cnf')
        write_options(self.mysql_config, defaults_file)
        add_exclusions(self.schema, defaults_file)

        # find the path to the mysqldump command
        mysqldump_bin = find_mysqldump(path=config['mysql-binpath'])
        LOG.info("Using mysqldump executable: %s", mysqldump_bin)

        # setup the mysqldump environment
        extra_defaults = config['extra-defaults']
        mysqldump = MySQLDump(defaults_file, 
                              mysqldump_bin, 
                              extra_defaults=extra_defaults)
        LOG.info("mysqldump version %s", '.'.join([str(digit)
                for digit in mysqldump.version]))
        options = collect_mysqldump_options(config, mysqldump, self.client)
        validate_mysqldump_options(mysqldump, options)

        os.mkdir(os.path.join(self.target_directory, 'backup_data'))

        try:
            try:
                start(mysqldump=mysqldump,
                      schema=self.schema,
                      lock_method=config['lock-method'],
                      file_per_database=config['file-per-database'],
                      open_stream=self._open_stream)
            except MySQLDumpError, exc:
                raise BackupError(str(exc))
        finally:
            if self.config['mysqldump']['stop-slave']:
                _start_slave(self.client, self.config['mysql:replication'])

    def _open_stream(self, path, mode):
        """Open a stream through the holland compression api, relative to
        this instance's target directory
        """
        path = os.path.join(self.target_directory, 'backup_data', path)
        compression_method = self.config['compression']['method']
        compression_level = self.config['compression']['level']
        if compression_method == 'none':
            compresison_info = '(uncompressed)'
        else:
            compression_info = '(%s compressed level %d)' % \
                                (compression_method, compression_level)
        stream = open_stream(path, mode, compression_method, compression_level)
        LOG.info("Saving mysqldump output to %s %s",
                os.path.basename(stream.name), compression_info)
        return stream

    def info(self):
        """Summarize information about this backup"""
        import textwrap
        return textwrap.dedent("""
        lock-method         = %s
        file-per-database   = %s

        Options used:
        flush-logs          = %s
        flush-privileges    = %s
        routines            = %s
        events              = %s

        Schema Filters:
        databases           = %s
        exclude-databases   = %s
        tables              = %s
        exclude-tables      = %s
        """).strip() % (
            self.config['mysqldump']['lock-method'],
            self.config['mysqldump']['file-per-database'] and 'yes' or 'no',
            self.config['mysqldump']['flush-logs'],
            self.config['mysqldump']['flush-privileges'],
            self.config['mysqldump']['dump-routines'],
            self.config['mysqldump']['dump-events'],
            ','.join(self.config['mysqldump']['databases']),
            ','.join(self.config['mysqldump']['exclude-databases']),
            ','.join(self.config['mysqldump']['tables']),
            ','.join(self.config['mysqldump']['exclude-tables'])
        )


def find_mysqldump(path=None):
    """Find a usable mysqldump binary in path or ENV[PATH]"""
    search_path = ':'.join(path) or os.environ.get('PATH', '')
    for _path in search_path.split(':'):
        if os.path.exists(os.path.join(_path, 'mysqldump')):
            return os.path.realpath(os.path.join(_path, 'mysqldump'))
    raise BackupError("Failed to find mysqldump in %s", search_path)

def collect_mysqldump_options(config, mysqldump, client):
    """Do intelligent collection of mysqldump options from the config
    and add any additional options for further validation"""
    options = []
    if config['flush-logs']:
        options.append('--flush-logs')
    if config['flush-privileges']:
        if mysqldump.version < (5,0,26):
            LOG.warning("--flush privileges is available only for mysqldump "
                        "in 5.0.26+")
        else:
            options.append('--flush-privileges')
    if config['dump-routines']:
        if mysqldump.version < (5, 0, 13):
            LOG.warning("--routines is not available before mysqldump 5.0.13+")
        else:
            if mysqldump.version < (5, 0, 20):
                LOG.warning("mysqldump will not dump DEFINER values before "
                            "version 5.0.20.  You are running mysqldump from "
                            "version %s", mysqldump.version_str)
            options.append('--routines')
    if config['dump-events']:
        if mysqldump.version < (5, 1, 8):
            LOG.warning("--events only available for mysqldump 5.1.8+. skipping")
        else:
            options.append('--events')
    if config['bin-log-position'] and client.show_variable('log_bin') == 'ON':
        options.append('--master-data=2')
    options.extend(config['additional-options'])
    return options

def validate_mysqldump_options(mysqldump, options):
    """Validate and add the requested options to the mysqldump instance"""
    error = False
    options = [opt for opt in options if opt]
    for option in options:
        try:
            mysqldump.add_option(option)
            LOG.info("Using mysqldump option %s", option)
        except MyOptionError, exc:
            LOG.warning(str(exc))


def _stop_slave(client, config=None):
    """Stop MySQL replication"""
    try:
        client.stop_slave()
        LOG.info("Stopped slave")
    except MySQLError, exc:
        raise BackupError("Failed to stop slave[%d]: %s" % exc.args)
    if config is not None:
        try:
            slave_info = client.show_slave_status()
            # update config with replication info
            config['slave_master_log_pos'] = slave_info['exec_master_log_pos']
            config['slave_master_log_file'] = slave_info['relay_master_log_file']
        except MySQLError, exc:
            raise BackupError("Failed to acquire slave status[%d]: %s" % \
                                exc.args)
        try:
            master_info = client.show_master_status()
            if master_info:
                config['master_log_file'] = master_info['file']
                config['master_log_pos'] = master_info['position']
        except MySQLError, exc:
            raise BackupError("Failed to acquire master status [%d] %s" % exc.args)

    LOG.info("MySQL Replication has been stopped.")

def _start_slave(client, config=None):
    """Start MySQL replication"""
    try:
        slave_info = client.show_slave_status()
        if slave_info and slave_info['exec_master_log_pos'] != config['slave_master_log_pos']:
            LOG.warning("ALERT! Slave position changed during backup")
    except MySQLError, exc:
        LOG.warning("Failed to sanity check replication[%d]: %s",
                         *exc.args)

    try:
        master_info = client.show_master_status()
        if master_info and master_info['position'] != config['master_log_pos']:
            LOG.warning("Sanity check on master status failed.  "
                    "Previously recorded %s:%s but currently found %s:%s",
                    config['master_log_file'], config['master_log_pos'],
                    master_info['file'], master_info['position'])
            LOG.warning("ALERT! Binary log position changed during backup!")
    except MySQLError, exc:
        LOG.warning("Failed to sanity check master status. [%d] %s", *exc.args)

    try:
        client.start_slave()
        LOG.info("Restarted slave")
    except MySQLError, exc:
        raise BackupError("Failed to restart slave [%d] %s" % exc.args)

def add_exclusions(schema, config):
    """Given a MySQLSchema add --ignore-table options in a [mysqldump]
    section for any excluded tables.

    """

    exclusions = []
    for db in schema.databases:
        if db.excluded:
            continue
        for table in db.tables:
            if table.excluded:
                LOG.info("Excluding table %s.%s", table.database, table.name)
                exclusions.append("ignore-table = " + table.database + '.' + table.name)

    if not exclusions:
        return

    try:
        my_cnf = open(config, 'a')
        print >>my_cnf
        print >>my_cnf, "[mysqldump]"
        for excl in exclusions:
            print >>my_cnf, excl
        my_cnf.close()
    except IOError, exc:
        LOG.error("Failed to write ignore-table exclusions to %s", config)
        raise

def parse_size(units_string):
    """Parse a MySQL-like size string into bytes
    
    >> parse_size('4G')
    4294967296
    """

    units_string = str(units_string)

    units = "kKmMgGtTpPeE"

    match = re.match(r'^(\d+(?:[.]\d+)?)([%s])$' % units, units_string)
    if not match:
        raise ValueError("Invalid constant size syntax %r" % units_string)
    number, unit = match.groups()
    unit = unit.upper()

    exponent = "KMGTPE".find(unit)

    return int(float(number) * 1024 ** (exponent + 1))
