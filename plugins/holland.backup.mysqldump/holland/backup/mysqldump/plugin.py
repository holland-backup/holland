"""Command Line Interface"""

from __future__ import print_function
import os
import re
import codecs
import logging
from holland.core.exceptions import BackupError
from holland.lib.compression import open_stream, lookup_compression
from holland.lib.mysql import MySQLSchema, connect, MySQLError
from holland.lib.mysql import include_glob, exclude_glob, \
                              include_glob_qualified, \
                              exclude_glob_qualified
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

exclude-invalid-views = boolean(default=no)

flush-logs           = boolean(default=no)
flush-privileges    = boolean(default=yes)
dump-routines       = boolean(default=yes)
dump-events         = boolean(default=yes)
stop-slave          = boolean(default=no)
max-allowed-packet  = string(default=128M)
bin-log-position    = boolean(default=no)

file-per-database   = boolean(default=yes)

additional-options  = force_list(default=list())

estimate-method = string(default='plugin')

[compression]
method = option('none', 'gzip', 'gzip-rsyncable', 'pigz', 'bzip2', 'pbzip2', 'lzma', 'lzop', 'gpg', default='gzip')
options = string(default="")
inline = boolean(default=yes)
level  = integer(min=0, max=9, default=1)

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

        self.schema.add_table_filter(include_glob_qualified(*config['tables']))
        self.schema.add_table_filter(exclude_glob_qualified(*config['exclude-tables']))
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
            except ValueError as exc:
                raise BackupError(str(exc))

        if estimate_method != 'plugin':
            raise BackupError("Invalid estimate-method '%s'" % estimate_method)

        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = MetadataTableIterator(self.client)
            try:
                self.client.connect()
            except Exception as ex:
                LOG.error("Failed to connect to database")
                LOG.error("%s", ex)
                raise BackupError("MySQL Error %s" % ex)
            try:
                self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            except MySQLError as exc:
                LOG.error("Failed to estimate backup size")
                LOG.error("[%d] %s", *exc.args)
                raise BackupError("MySQL Error [%d] %s" % exc.args)
            return float(sum([db.size for db in self.schema.databases]))
        finally:
            self.client.disconnect()

    def _fast_refresh_schema(self):
        # determine if we can skip expensive table metadata lookups entirely
        # and just worry about finding database names
        # However, with lock-method=auto-detect we must look at table engines
        # to determine what lock method to use
        config = self.config['mysqldump']
        fast_iterate = config['lock-method'] != 'auto-detect' and \
                        not config['exclude-invalid-views']

        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = SimpleTableIterator(self.client, record_engines=True)
            try:
                self.client.connect()
                self.schema.refresh(db_iter=db_iter,
                                    tbl_iter=tbl_iter,
                                    fast_iterate=fast_iterate)
            except MySQLError as exc:
                LOG.debug("MySQLdb error [%d] %s", exc_info=True, *exc.args)
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
            if self.config['mysqldump']['stop-slave']:
                self.client = connect(self.mysql_config['client'])
                if self.client.show_slave_status()['slave_sql_running'] != 'Yes':
                    raise BackupError("stop-slave enabled, but replication is "
                                  "either not configured or the slave is not "
                                  "running.")
                self.config.setdefault('mysql:replication', {})
                _stop_slave(self.client, self.config['mysql:replication'])
            self._backup()
        except Exception as ex:
                LOG.debug(ex)
        finally:
            if self.config['mysqldump']['stop-slave'] and \
                'mysql:replication' in self.config:
                _start_slave(self.client, self.config['mysql:replication'])
            if mock_env:
                mock_env.restore_environment()

    def _backup(self):
        """Real backup method.  May raise BackupError exceptions"""
        config = self.config['mysqldump']

        # setup defaults_file with ignore-table exclusions
        defaults_file = os.path.join(self.target_directory, 'my.cnf')
        write_options(self.mysql_config, defaults_file)
	LOG.debug('Got Here')
        if config['exclude-invalid-views']:
            LOG.info("* Finding and excluding invalid views...")
            definitions_path = os.path.join(self.target_directory,
                                            'invalid_views.sql')
            exclude_invalid_views(self.schema, self.client, definitions_path)
        add_exclusions(self.schema, defaults_file)
        # find the path to the mysqldump command
        mysqldump_bin = find_mysqldump(path=config['mysql-binpath'])
        LOG.info("Using mysqldump executable: %s", mysqldump_bin)
        # setup the mysqldump environment
        extra_defaults = config['extra-defaults']
        try:
            mysqldump = MySQLDump(defaults_file, 
                                  mysqldump_bin, 
                                  extra_defaults=extra_defaults)
        except MySQLDumpError as exc:
            raise BackupError(str(exc))
        except Exception as ex:
            LOG.warning(ex)
        LOG.info("mysqldump version %s", '.'.join([str(digit)
                for digit in mysqldump.version]))
        options = collect_mysqldump_options(config, mysqldump, self.client)
        validate_mysqldump_options(mysqldump, options)

        os.mkdir(os.path.join(self.target_directory, 'backup_data'))

        if self.config['compression']['method'] != 'none' and \
            self.config['compression']['level'] > 0:
            try:
                cmd, ext = lookup_compression(self.config['compression']['method'])
            except OSError as exc:
                raise BackupError("Unable to load compression method '%s': %s" %
                                  (self.config['compression']['method'], exc))
            LOG.info("Using %s compression level %d with args %s",
                     self.config['compression']['method'],
                     self.config['compression']['level'],
                     self.config['compression']['options'])
        else:
            LOG.info("Not compressing mysqldump output")
            cmd = ''
            ext = ''

        try:
            start(mysqldump=mysqldump,
                  schema=self.schema,
                  lock_method=config['lock-method'],
                  file_per_database=config['file-per-database'],
                  open_stream=self._open_stream,
                  compression_ext=ext)
        except MySQLDumpError as exc:
            raise BackupError(str(exc))

    def _open_stream(self, path, mode, method=None):
        """Open a stream through the holland compression api, relative to
        this instance's target directory
        """
        path = os.path.join(self.target_directory, 'backup_data', path)
        compression_method = method or self.config['compression']['method']
        compression_level = self.config['compression']['level']
        compression_options = self.config['compression']['options']
        stream = open_stream(path,
                             mode,
                             compression_method,
                             compression_level,
                             extra_args=compression_options)
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
        if os.path.isfile(_path):
            return os.path.realpath(_path)
        if os.path.exists(os.path.join(_path, 'mysqldump')):
            return os.path.realpath(os.path.join(_path, 'mysqldump'))
    raise BackupError("Failed to find mysqldump in %s" % search_path)

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
    if config['max-allowed-packet']:
        options.append('--max-allowed-packet=' + config['max-allowed-packet'])
    if config['bin-log-position']:
        if client.show_variable('log_bin') != 'ON':
            raise BackupError("bin-log-position requested but "
                              "bin-log on server not active")
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
        except MyOptionError as exc:
            LOG.warning(str(exc))


def _stop_slave(client, config=None):
    """Stop MySQL replication"""
    try:
        client.stop_slave(sql_thread_only=True)
        LOG.info("Stopped slave")
    except MySQLError as exc:
        raise BackupError("Failed to stop slave[%d]: %s" % exc.args)
    if config is not None:
        try:
            slave_info = client.show_slave_status()
            if slave_info:
                # update config with replication info
                config['slave_master_log_pos'] = slave_info['exec_master_log_pos']
                config['slave_master_log_file'] = slave_info['relay_master_log_file']
        except MySQLError as exc:
            raise BackupError("Failed to acquire slave status[%d]: %s" % \
                                exc.args)
        try:
            master_info = client.show_master_status()
            if master_info:
                config['master_log_file'] = master_info['file']
                config['master_log_pos'] = master_info['position']
        except MySQLError as exc:
            raise BackupError("Failed to acquire master status [%d] %s" % exc.args)

    LOG.info("MySQL Replication has been stopped.")

def _start_slave(client, config=None):
    """Start MySQL replication"""
    try:
        slave_info = client.show_slave_status()
        if slave_info and slave_info['exec_master_log_pos'] != config['slave_master_log_pos']:
            LOG.warning("Sanity check on slave status failed.  "
                    "Previously recorded %s:%s but currently found %s:%s",
                    config['slave_master_log_file'], config['slave_master_log_pos'],
                    slave_info['relay_master_log_file'], slave_info['exec_master_log_pos'])
            LOG.warning("ALERT! Slave position changed during backup!")
    except MySQLError as exc:
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
    except MySQLError as exc:
        LOG.warning("Failed to sanity check master status. [%d] %s", *exc.args)

    try:
        client.start_slave()
        LOG.info("Restarted slave")
    except MySQLError as exc:
        raise BackupError("Failed to restart slave [%d] %s" % exc.args)

def exclude_invalid_views(schema, client, definitions_file):
    """Flag invalid MySQL views as excluded to skip them during a mysqldump
    """
    sqlf = open(definitions_file, 'w')
    LOG.info("* Invalid and excluded views will be saved to %s",
            definitions_file)
    cursor = client.cursor()
    try:
        print("--", file=sqlf)
        print("-- DDL of Invalid Views", file=sqlf)
        print("-- Created automatically by Holland", file=sqlf)
        print("--", file=sqlf)
        print(file=sqlf)
        for db in schema.databases:
            if db.excluded:
                continue
            for table in db.tables:
                if table.excluded:
                    continue
                if table.engine != 'view':
                    continue
                LOG.debug("Testing view %s.%s", db.name, table.name)
                invalid_view = False
                try:
                    cursor.execute('SHOW FIELDS FROM `%s`.`%s`' %
                                    (db.name, table.name))
                    # check for missing definers that would bork
                    # lock-tables
                    for _, error_code, msg in client.show_warnings():
                        if error_code == 1449: # ER_NO_SUCH_USER
                            raise MySQLError(error_code, msg)
                except MySQLError as exc:
                    # 1356 = View references invalid table(s)...
                    if exc.args[0] in (1356, 1142, 1143, 1449, 1267, 1271):
                        invalid_view = True
                    else:
                        LOG.error("Unexpected error when checking invalid "
                                  "view %s.%s: [%d] %s",
                                  db.name,
                                  table.name,
                                  *exc.args)
                        raise BackupError("[%d] %s" % exc.args)
                if invalid_view:
                    LOG.warning("* Excluding invalid view `%s`.`%s`: [%d] %s",
                                db.name, table.name, *exc.args)
                    table.excluded = True
                    view_definition = client.show_create_view(db.name,
                                                              table.name,
                                                              use_information_schema=True)
                    if view_definition is None:
                        LOG.error("!!! Failed to retrieve view definition for "
                                  "`%s`.`%s`", db.name, table.name)
                        LOG.warning("!!! View definition for `%s`.`%s` will "
                                    "not be included in this backup", db.name,
                                    table.name)
                        continue

                    LOG.info("* Saving view definition for "
                                 "`%s`.`%s`",
                                 db.name, table.name)
                    print("--", file=sqlf)
                    print("-- Current View: `%s`.`%s`" % \
                    (db.name, table.name), file=sqlf)
                    print("--", file=sqlf)
                    print(file=sqlf)
                    print(view_definition + ';', file=sqlf)
                    print(file=sqlf)
    finally:
        sqlf.close()

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
        my_cnf = codecs.open(config, 'a', 'utf8')
        print(file=my_cnf)
        print("[mysqldump]", file=my_cnf)
        for excl in exclusions:
            print(excl, file=my_cnf)
        my_cnf.close()
    except IOError as exc:
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
