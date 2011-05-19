"""
holland.backup.mysqldump.util

Utility functions to support mysqldump backups

:copyright: 2008-2011 Rackspace US, Inc.
:license: GPLv2, see LICENSE for details
"""
import os
import codecs
import logging
from subprocess import Popen, PIPE, STDOUT
from holland.core import BackupError
from holland.core.stream import open_stream, load_stream_plugin
from holland.core.util.safefilename import encode
from holland.lib.mysql import MySQLSchema, MySQLError
from holland.lib.mysql import DatabaseIterator, MetadataTableIterator
from holland.lib.mysql import include_glob, exclude_glob, \
                              include_glob_qualified, \
                              exclude_glob_qualified

LOG = logging.getLogger(__name__)

def server_version(client):
    """Retrieve the server version from a connection

    >> client = MySQLClient(read_default_group='client')
    >> client.server_version()
    (5, 5, 11)

    :param client: A holland.lib.mysql.client:Client instance
    :returns: tuple of integers representing the server version
    """
    try:
        client.connect()
        version = client.get_server_info()
        return tuple([int(x)
                      for x in version.split('-', 1)[0].split('.')])
    except MySQLError, exc:
        raise BackupError("[%d] %s" % exc.args)

def schema_from_config(config):
    """Build a MySQLSchema instance from a MySQLDumpBackupPlugin config

    :param config: holland.core:Config instance

    :returns: holland.lib.mysql:MySQLSchema instance
    """
    schema = MySQLSchema()
    schema.add_database_filter(include_glob(*config['databases']))
    schema.add_database_filter(exclude_glob(*config['exclude-databases']))
    schema.add_table_filter(include_glob_qualified(*config['tables']))
    schema.add_table_filter(exclude_glob_qualified(*config['exclude-tables']))
    schema.add_engine_filter(include_glob(*config['engines']))
    schema.add_engine_filter(exclude_glob(*config['exclude-engines']))
    schema.add_transactional_engines(config['transactional-engines-override'])
    schema.add_transactional_databases(
            config['transactional-databases-override']
    )
    schema.add_transactional_tables(config['transactional-tables-override'])
    return schema

def check_transactional(databases):
    """Check whether all of the given databases are transactional

    :param databases: list of holland.lib.mysql:Database instances
    :raises: BackupError if one or more databases had non-transactional tables
    """
    non_txn_dbs = [db for db in databases
                   if not db.is_transactional and not db.excluded]

    if non_txn_dbs:
        for db in non_txn_dbs:
            LOG.error("Database '%s' has one or more non-transactional tables:",
                      db.name)
            for table in db.tables:
                LOG.error("  * %s.%s is non-transactional (engine=%s)",
                          db.name, table.name, table.engine)
        raise BackupError("One or more databases had non-transactional tables "
                          "that would result in a locking backup but "
                          "lockless-only was requested.  Aborting backup.")


def check_mysqldump_version(mysqldump, mysqld_version):
    """Check the version of a mysqldump binary compared to a mysql server
    version

    This runs mysqldump --version and parses out the version string
    returning a tuple of integers representing that version

    >> check_mysqldump_version('/usr/bin/mysqldump', (5,5,11))

    :param mysqldump: location of a mysqldump binary
    :param mysqld_version: tuple version of the mysql server
    """
    stdout = Popen([mysqldump, '--version'],
                   stdout=PIPE, stderr=STDOUT,
                   close_fds=True).communicate()[0]
    version = tuple(map(int, stdout.split()[4].split(',', 1)[0].split('.')))
    if version[0:2] < mysqld_version[0:2]:
        LOG.warning("%s is over a major version behind the mysql server %s",
                    version, mysqld_version)
    elif version != mysqld_version:
        LOG.warning("version mismatch: mysqldump %s != mysqld %s",
                    version, mysqld_version)

def argv_from_config(defaults_file, config, mysqld_version):
    """Generate a list of arguments to mysqldump from a MySQLDumpPlugin config

    :param defaults_file: the my.cnf location to pass to mysqldump
    :param config: a holland.core:Config instance containing the mysqldump
                   configuration
    :param mysqld_version: version of the mysql server
    :returns: list of strings suitable for passing to subprocess.Popen
    """
    mysqldump = locate_mysqldump(config['mysqldump']['mysql-binpath'])
    check_mysqldump_version(mysqldump, mysqld_version)
    mysqldump_options = mysqldump_options_from_config(config['mysqldump'],
                                                      mysqld_version)
    if config['mysqldump']['extra-defaults']:
        defaults_option = '--defaults-extra-file'
    else:
        defaults_option = '--defaults-file'

    return [
        mysqldump,
        defaults_option + '=' + defaults_file,
    ] + mysqldump_options

# XXX: this should be generated relative to the mysqldump version, not the
# server
def mysqldump_options_from_config(config, server_version):
    """Generate a list of mysqldump options from a config

    This adds options suitable to a particular version of mysqldump

    :param config: mysqldump plugin config options
    :param server_version: version of MySQL server being targetted
    :returns: list of options
    """
    LOG.info("- Adding mysqldump options")
    options = []
    if config['flush-logs']:
        LOG.info("+ --flush-logs")
        options.append('--flush-logs')
    if config['bin-log-position']:
        LOG.info("+ --master-data=2")
        options.append('--master-data=2')
    if config['flush-privileges']:
        if server_version < (5, 0):
            LOG.info("! flush-privileges not supported")
        else:
            LOG.info("+ --flush-privileges")
            options.append('--flush-privileges')
    if config['dump-routines']:
        if server_version < (5, 0):
            LOG.info("! routines not supported")
        else:
            LOG.info("+ --routines")
            options.append('--routines')
    if config['dump-events']:
        if server_version < (5, 1):
            LOG.info("! events not supported")
        else:
            LOG.info("+ --events")
            options.append('--events')
    if config['max-allowed-packet']:
        LOG.info("+ --max-allowed-packet=%s", config['max-allowed-packet'])
        options.append('--max-allowed-packet=%s' % config['max-allowed-packet'])
    for option in config['additional-options']:
        if option:
            LOG.info("+ custom option:: %s", option)
            options.append(option)
    return options

def generate_manifest(path, schema, config):
    """Generate a simple text file mapping database names to file names

    This is used in case a database name was encoded to something not very
    readable.  This can happen if a database has filename unfriendly characters
    such as '/' or for unicode usage.

    """
    path = os.path.join(path, 'backup_data', 'MANIFEST.txt')
    method = config['compression']['method']
    level = config['compression']['level']
    fileobj = codecs.open(path, 'w', encoding='utf8')
    try:
        for database in schema.databases:
            name = encode(database.name)[0]
            stream = load_stream_plugin(method)
            print >> fileobj, database.name, \
                  stream.stream_info(name + '.sql', method)['name']
    finally:
        fileobj.close()

def log_host_info(client):
    """Log information about how a connection is connected to MySQL"""
    host = client.get_host_info().lower()
    if 'socket' in host:
        host = '%s %s' % (host, client.show_variable('socket'))
    else:
        host = '%s port %s' % (host, client.show_variable('port'))
    user = client.current_user()
    LOG.info("Connected to %s as %s", host, user)

def client_from_config(config):
    """Create a client connect to MySQL from a mysqldump plugin config

    :returns: client instance
    """
    from holland.lib.mysql import connect, build_mysql_config, PassiveMySQLClient
    try:
        config = build_mysql_config(config)
        LOG.debug("client_from_config => %r", config)
        return connect(config['client'], client_class=PassiveMySQLClient,
                       read_default_group='client')
    except:
        # parse error of defaults-extra-files, for instance
        raise BackupError("Failed to create client")

def refresh_schema(schema, client):
    "Disregard performance. Acquire metadata."
    try:
        client.connect()
        db_iter = DatabaseIterator(client)
        tbl_iter = MetadataTableIterator(client)
        schema.refresh(db_iter, tbl_iter)
    except MySQLError, exc:
        raise BackupError("Failed to refresh schema: %s" % exc)

def locate_mysqldump(search_path):
    """Find a valid mysqldump binary from a given search path

    :returns: string path to a mysqldump binary
    """
    from holland.lib.which import which, WhichError
    if not search_path:
        try:
            return which('mysqldump')
        except WhichError:
            raise BackupError("mysqldump not found")
    else:
        for path in search_path:
            if os.path.isfile(path):
                return path
            else:
                path = os.path.join(path, 'mysqldump')
                if os.path.isfile(path):
                    return path
        raise BackupError("mysqldump not found")

def lock_method_from_config(config):
    """Determine the correct mysqldump lock option from the config

    :returns: lock option or None if it should be autodetected
    """
    lock_method = config['mysqldump']['lock-method']
    if lock_method == 'auto-detect':
        return None # runner will determine this based on databases
    elif lock_method == 'single-transaction':
        return '--single-transaction'
    elif lock_method == 'lock-tables':
        return '--lock-tables'
    elif lock_method == 'flush-lock':
        return '--lock-all-tables'
    elif lock_method == 'none':
        return '--skip-lock-tables'
    else:
        raise ValueError("Invalid lock method '%s'" % lock_method)

def defaults_from_config(config, path):
    """Generate a my.cnf file from config options

    :param config: mysql config options
    :param path: path where the config should be written
    :returns: path to config option
    """
    from holland.lib.mysql import build_mysql_config, write_options
    path = os.path.join(path, 'holland.my.cnf')
    mysql_config = build_mysql_config(config)
    write_options(mysql_config, path)
    return path

def stop_slave(client):
    """Stop a MySQL slave

    :returns: dictionary with values from SHOW SLAVE STATUS
    """
    try:
        client.connect()
        client.stop_slave(sql_thread_only=True)
        status = client.show_slave_status()
    finally:
        client.disconnect()
    return status

def record_slave_status(status, config):
    """Record slave status into a given config dictionary"""
    master_log_file = status['relay_master_log_file']
    master_log_pos  = status['exec_master_log_pos']
    section = config.setdefault('mysql:replication', {})
    section['master-log-file'] = master_log_file
    section['master-log-pos']  = master_log_pos

def start_slave(client):
    """Start a MySQL slave"""
    try:
        client.connect()
        client.start_slave()
    finally:
        client.disconnect()

def sql_open(base_path, config):
    """Create a function suitable for opening files relative to a given path

    The provided method will encode the requested filename and open a file
    object relative to some base path.

    :returns: open method
    """
    def _open(name, mode):
        """Delegate an open operation to holland's stream API"""
        name = encode(name)[0]
        real_path = os.path.join(base_path, name + '.sql')
        return open_stream(real_path, 'w',
                           method=config['method'],
                           level=config['level'])
    return _open

def write_exclusions(path, schema):
    """Write excluded tables in a schema to a my.cnf file

    These exclusions are written as --ignore-table options for
    mysqldump in order to skip dumping particular tables.
    """
    fileobj = codecs.open(path, 'a', encoding='utf8')
    try:
        print >> fileobj, "[mysqldump]"
        for table in schema.excluded_tables:
            print >> fileobj, "ignore-table=%s.%s" % \
                    (table.database, table.name)
    finally:
        fileobj.close()
