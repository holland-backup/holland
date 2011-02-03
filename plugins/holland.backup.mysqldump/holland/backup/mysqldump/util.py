import os
import codecs
import logging

LOG = logging.getLogger(__name__)

def server_version(client):
    from holland.lib.mysql import MySQLError
    try:
        client.connect()
        return tuple(map(int, client.get_server_info().split('-', 1)[0].split('.')))
    except MySQLError, exc:
        raise BackupError("[%d] %s" % exc.args)

def schema_from_config(config):
    from holland.lib.mysql import MySQLSchema
    from holland.lib.mysql import include_glob, exclude_glob
    from holland.lib.mysql import include_glob_qualified, \
                                  exclude_glob_qualified
    schema = MySQLSchema()
    schema.add_database_filter(include_glob(*config['databases']))
    schema.add_database_filter(exclude_glob(*config['exclude-databases']))
    LOG.info("+ Excluding: %s", ','.join(config['exclude-databases']))
    schema.add_table_filter(include_glob_qualified(*config['tables']))
    schema.add_table_filter(exclude_glob_qualified(*config['exclude-tables']))
    schema.add_engine_filter(include_glob(*config['engines']))
    schema.add_engine_filter(exclude_glob(*config['exclude-engines']))
    return schema

def check_mysqldump_version(mysqldump, mysqld_version):
    from subprocess import Popen, PIPE, STDOUT
    stdout = Popen([mysqldump, '--version'],
                   stdout=PIPE, stderr=STDOUT,
                   close_fds=True).communicate()[0]
    version = tuple(map(int, stdout.split()[4].split(',', 1)[0].split('.')))
    if version[0:2] < mysqld_version[0:2]:
        LOG.warning("%s is over a major version behind the mysql server %s",
                    version, mysqld_version)
    elif version != mysqld_version:
        LOG.warning("verson mismatch: mysqldump %s != mysqld %s",
                    version, mysqld_version)

def argv_from_config(defaults_file, config, mysqld_version):
    mysqldump = locate_mysqldump(config['mysqldump']['mysql-binpath'])
    check_mysqldump_version(mysqldump, mysqld_version)
    mysqldump_options = mysqldump_options_from_config(config['mysqldump'],
                                                      mysqld_version)
    return [
        mysqldump,
        '--defaults-file=' + defaults_file,
    ] + mysqldump_options

def mysqldump_options_from_config(config, server_version):
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
    from holland.core.stream import load_stream_plugin
    from holland.lib.safefilename import encode
    path = os.path.join(path, 'backup_data', 'MANIFEST.txt')
    method = config['compression']['method']
    level = config['compression']['level']
    fileobj = codecs.open(path, 'w', encoding='utf8')
    try:
        for database in schema.databases:
            name = encode(database.name)[0]
            stream = load_stream_plugin(method)(method)
            print >> fileobj, database.name, \
                  stream.stream_info(name + '.sql', method)['name']
    finally:
        fileobj.close()

def client_from_config(config):
    from holland.lib.mysql import connect, build_mysql_config, PassiveMySQLClient
    try:
        config = build_mysql_config(config)
        LOG.debug("client_from_config => %r", config)
        return connect(config['client'], client_class=PassiveMySQLClient)
    except:
        # parse error of defaults-extra-files, for instance
        raise BackupError("Failed to create client")

def parse_size(value):
    """Parse a MySQL size into integer bytes
    :param value: str value to parse
    :returns: integer number of bytes
    :rtype: int
    """
    units = "kKmMgGtTpPeE"
    match = re.match(r'^(\d+(?:[.]\d+)?)([%s])$' % units, value)
    if not match:
        raise ValueError("Invalid constant size syntax %r" % value)
    number, unit = match.groups()
    unit = unit.upper()

    exponent = "KMGTPE".find(unit)

    return int(float(number) * 1024 ** (exponent + 1))

def refresh_schema(schema, client):
    "Disregard performance. Acquire metadata."
    from holland.lib.mysql import MySQLError
    from holland.lib.mysql import DatabaseIterator, MetadataTableIterator
    try:
        client.connect()
        db_iter = DatabaseIterator(client)
        tbl_iter = MetadataTableIterator(client)
        schema.refresh(db_iter, tbl_iter)
    except MySQLError, exc:
        raise BackupError("Failed to refresh schema: %s" % exc)

def locate_mysqldump(search_path):
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
    lock_method = config['mysqldump']['lock-method']
    if lock_method == 'auto-detect':
        return None # runner will determine this based on databases
    elif lock_method == 'single-transaction':
        return '--single-transaction'
    elif lock_method == 'lock-tables':
        return '--lock-tables'
    elif lock_method == 'flush-lock':
        return '--lock-all-tables'
    else:
        raise ValueError("Invalid lock method '%s'" % lock_method)

def defaults_from_config(config, path):
    from holland.lib.mysql import build_mysql_config, write_options
    path = os.path.join(path, 'holland.my.cnf')
    mysql_config = build_mysql_config(config)
    write_options(mysql_config, path)
    return path

def stop_slave(client):
    try:
        client.connect()
        client.stop_slave(sql_thread_only=True)
        status = client.show_slave_status()
    finally:
        client.disconnect()
    return status

def record_slave_status(status, config):
    master_log_file = status['relay_master_log_file']
    master_log_pos  = status['exec_master_log_pos']
    section = config.setdefault('mysql:replication', {})
    section['master-log-file'] = master_log_file
    section['master-log-pos']  = master_log_pos

def start_slave(client):
    try:
        client.connect()
        client.start_slave()
    finally:
        client.disconnect()

def sql_open(base_path, config):
    from holland.core.stream import open_stream
    from holland.lib.safefilename import encode
    def _open(name, mode):
        name = encode(name)[0]
        real_path = os.path.join(base_path, name + '.sql')
        return open_stream(real_path, 'w',
                           method=config['method'],
                           level=config['level'])
    return _open

def write_exclusions(path, schema):
    fileobj = codecs.open(path, 'a', encoding='utf8')
    try:
        print >>fileobj, "[mysqldump]"
        for table in schema.excluded_tables:
            print >> fileobj, "ignore-table=%s.%s" % \
                    (table.database, table.name)
    finally:
        fileobj.close()
