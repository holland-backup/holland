"""Command Line Interface"""

import os
import logging
from holland.core.exceptions import BackupError
from holland.lib.compression import open_stream
from holland.lib.mysql import MySQLSchema, include_glob, exclude_glob, \
			      DatabaseIterator, TableIterator, connect, MySQLError
from holland.backup.mysqldump.base import start
from holland.backup.mysqldump.util import INIConfig, update_config
from holland.backup.mysqldump.util.ini import OptionLine, CommentLine
from holland.backup.mysqldump.mysql.option import load_options, write_options
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

        self.mysql_config = make_mysql_config(self.config['mysql:client'])
        self.client = connect(self.mysql_config['client'])

    def estimate_backup_size(self):
        """Estimate the size of the backup this plugin will generate"""
        try:
            self.client.connect()
            db_iter = DatabaseIterator(self.client)
            tbl_iter = TableIterator(self.client)
            try:
                self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            except MySQLError, exc:
                raise BackupError("Failed to estimate backup size from MySQL metadata")
            return sum([db.size for db in self.schema.databases])
        finally:
            self.client.disconnect()

    def backup(self):
        """Run a MySQL backup"""

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
        add_exclusions(self.schema, self.mysql_config)
        defaults_file = os.path.join(self.target_directory, 'my.cnf')
        write_options(self.mysql_config, defaults_file)

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
            self.config.mysqldump.flush_logs,
            self.config.mysqldump.flush_privileges,
            self.config.mysqldump.dump_routines,
            self.config.mysqldump.dump_events,
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

def make_mysql_config(mysql_config):
    """Given a mysql:client config, create a config object
    that represents the auth parameters"""
    defaults_config = INIConfig()
    defaults_config._new_namespace('client')
    for config in mysql_config['defaults-extra-file']:
        LOG.info("Loading %s [%s]", config, os.path.expanduser(config))
        _my_config = load_options(config)
        update_config(defaults_config, _my_config)

    for key in ('user', 'password', 'socket', 'host', 'port'):
        if key in mysql_config and mysql_config[key]:
            defaults_config['client'][key] = mysql_config[key]
    return defaults_config

def add_exclusions(schema, config):
    """Given a MySQLSchema add --ignore-table options in a [mysqldump]
    section for any excluded tables.

    This will also add comments detailing any databases that are entirely
    skipped
    """
    section = config._new_namespace('mysqldump')
    for db in schema.databases:
        if db.excluded:
            LOG.info("Excluding entire %s database", db.name)
            section._lines[0].contents.append(CommentLine("database '%s' excluded"))
        for table in db.tables:
            if table.excluded:
                LOG.info("Excluding table %s.%s", table.database, table.name)
                section._lines[0].contents.append(OptionLine("ignore-table", table.database + '.' + table.name))
