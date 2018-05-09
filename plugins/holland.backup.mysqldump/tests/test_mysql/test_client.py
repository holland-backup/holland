import sys
from holland.backup.mysqldump.mock.mocker import Mocker, ANY, ARGS, KWARGS
from holland.backup.mysqldump.mysql.client import MySQLClient, flatten_list
from nose.tools import assert_equals

mocker =  None
def _db_setup():
    global mocker
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    mock = connect(ARGS, KWARGS)
    mocker.result(mock)
    cursor = mock.cursor()
    cursor.execute(ANY)
    cursor.close()
    mocker.replay()

def _db_teardown():
    global mocker
    mocker.verify()
    mocker.restore()
    mocker = None

def test_flush_tables():
    client = MySQLClient(read_default_group='client')
    client.flush_tables()
test_flush_tables.setup = _db_setup
test_flush_tables.teardown = _db_teardown

def test_flush_tables_with_read_lock():
    client = MySQLClient(read_default_group='client')
    client.flush_tables_with_read_lock()
test_flush_tables_with_read_lock.setup = _db_setup
test_flush_tables_with_read_lock.teardown = _db_teardown

def test_unlock_tables():
    client = MySQLClient(read_default_group='client')
    client.unlock_tables()
test_unlock_tables.setup = _db_setup
test_unlock_tables.teardown = _db_teardown

def test_stop_slave():
    client = MySQLClient(read_default_group='client')
    client.stop_slave()
test_stop_slave.setup = _db_setup
test_stop_slave.teardown = _db_teardown

def test_start_slave():
    client = MySQLClient(read_default_group='client')
    client.start_slave()
test_start_slave.setup = _db_setup
test_start_slave.teardown = _db_teardown

def test_flatten_list():
    start = ['aaa', ['bb', 'ccccc']]
    expected = ['aaa', 'bb', 'ccccc']
    assert_equals(flatten_list(start), expected)

def test_show_databases():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    cursor.execute('SHOW DATABASES')
    cursor.fetchall()
    mocker.result(['mysql', 'test'])
    cursor.close()
    mocker.replay()
    try:
        client = MySQLClient()
        databases = client.show_databases()
        assert_equals(databases, ['mysql', 'test'])
    finally:
        mocker.restore()

def test_show_tables():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    cursor.execute('SHOW TABLES FROM `mysql`')
    iter(cursor)
    mocker.generate(['user', 'db'])
    cursor.close()
    mocker.replay()

    try:
        client = MySQLClient()
        tables = client.show_tables('mysql')
        assert_equals(tables, ['user', 'db'])
    finally:
        mocker.restore()

def test_50_metadata():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    link.get_server_info()
    mocker.result('5.0.87')
    cursor = link.cursor()
    cursor.execute('SHOW TABLE STATUS FROM `mysql`')
    cursor.description
    fields = [('name',),('engine',),('data_length',),('index_length',)]
    mocker.result(fields)
    iter(cursor)
    results = [
        ('user', 'myisam',1024,1024),
        ('db', 'myisam', 1024, 1024),
    ]
    mocker.generate(results)
    cursor.close()
    mocker.replay()
    try:
        client = MySQLClient(read_default_file='/etc/my.cnf')
        expected_metadata = [
            { 'database' : 'mysql',
              'name' : 'user',
              'engine' : 'myisam',
              'data_size' : 1024,
              'index_size' : 1024,
              'is_transactional' : False
            },
            { 'database' : 'mysql',
              'name' : 'db',
              'engine' : 'myisam',
              'data_size' : 1024,
              'index_size' : 1024,
              'is_transactional' : False
            },
        ]
        md = client.show_table_metadata('mysql')
        assert_equals(md, expected_metadata)
        mocker.verify()
    finally:
        mocker.restore()

def test_51_metadata():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    link.get_server_info()
    mocker.result('5.1.99')
    cursor = link.cursor()
    sql = ("SELECT TABLE_SCHEMA AS `database`, "
           "          TABLE_NAME AS `name`, "
           "          DATA_LENGTH AS `data_size`, "
           "          INDEX_LENGTH AS `index_size`, "
           "          ENGINE AS `engine`, "
           "          TRANSACTIONS AS `is_transactional` "
           "FROM INFORMATION_SCHEMA.TABLES "
           "JOIN INFORMATION_SCHEMA.ENGINES USING (ENGINE) "
           "WHERE TABLE_SCHEMA = %s")
    cursor.execute(sql, ('mysql'))
    cursor.description
    fields = [('database',),('name',),('data_size',),('index_size',),('engine',),('is_transactional',)]
    mocker.result(fields)
    cursor.fetchall()
    results = [
        ('mysql', 'user', 1024,1024, 'MyISAM', False),
        ('mysql', 'db', 1024, 1024, 'MyISAM', False),
    ]
    mocker.result(results)
    cursor.close()
    mocker.replay()
    try:
        client = MySQLClient(read_default_file='/etc/my.cnf')
        expected_metadata = [
            { 'database' : 'mysql',
              'name' : 'user',
              'engine' : 'MyISAM',
              'data_size' : 1024,
              'index_size' : 1024,
              'is_transactional' : False,
            },
            { 'database' : 'mysql',
              'name' : 'db',
              'engine' : 'MyISAM',
              'data_size' : 1024,
              'index_size' : 1024,
              'is_transactional' : False,
            },
        ]
        md = client.show_table_metadata('mysql')
        assert_equals(md, expected_metadata)
        mocker.verify()
    finally:
        mocker.restore()

def test_show_slave_status():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    sql = 'SHOW SLAVE STATUS'
    cursor.execute(sql)
    cursor.description
    fields = (
        ('Slave_IO_State',),
        ('Master_Host',),
        ('Master_User',),
        ('Master_Port',),
        ('Connect_Retry',),
        ('Master_Log_File',),
        ('Read_Master_Log_Pos',),
        ('Relay_Log_File',),
        ('Relay_Log_Pos',),
        ('Relay_Master_Log_File',),
        ('Slave_IO_Running',),
        ('Slave_SQL_Running',),
        ('Replicate_Do_DB',),
        ('Replicate_Ignore_DB',),
        ('Replicate_Do_Table',),
        ('Replicate_Ignore_Table',),
        ('Replicate_Wild_Do_Table',),
        ('Replicate_Wild_Ignore_Table',),
        ('Last_Errno',),
        ('Last_Error',),
        ('Skip_Counter',),
        ('Exec_Master_Log_Pos',),
        ('Relay_Log_Space',),
        ('Until_Condition',),
        ('Until_Log_File',),
        ('Until_Log_Pos',),
        ('Master_SSL_Allowed',),
        ('Master_SSL_CA_File',),
        ('Master_SSL_CA_Path',),
        ('Master_SSL_Cert',),
        ('Master_SSL_Cipher',),
        ('Master_SSL_Key',),
        ('Seconds_Behind_Master',),
        ('Master_SSL_Verify_Server_Cert',),
        ('Last_IO_Errno',),
        ('Last_IO_Error',),
        ('Last_SQL_Errno',),
        ('Last_SQL_Error',),
    )
    mocker.result(fields)
    cursor.fetchone()
    result = (
        'Waiting for master to send event',
        '127.0.0.1',
        'msandbox',
        23351,
        60,
        'mysql-bin.000004',
        106,
        'mysql_sandbox23353-relay-bin.001724',
        251,
        'mysql-bin.000004',
        'Yes',
        'Yes',
        '',
        '',
        '',
        '',
        '',
        '',
        0,
        '',
        0,
        106,
        564,
        'None',
        '',
        0,
        'No',
        '',
        '',
        '',
        '',
        '',
        0,
        'No',
        0,
        '',
        0,
        ''
    )
    mocker.result(result)
    cursor.close()
    mocker.replay()
    try:
        client = MySQLClient(read_default_file='/etc/my.cnf')
        expected_status = dict(list(zip([f[0].lower() for f in fields], result)))
        slave_status = client.show_slave_status()
        assert_equals(slave_status, expected_status)
        mocker.verify()
    finally:
        mocker.restore()

def test_show_slave_status_noslave():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    sql = 'SHOW SLAVE STATUS'
    cursor.execute(sql)
    cursor.description
    fields = (
        ('Slave_IO_State',),
        ('Master_Host',),
        ('Master_User',),
        ('Master_Port',),
        ('Connect_Retry',),
        ('Master_Log_File',),
        ('Read_Master_Log_Pos',),
        ('Relay_Log_File',),
        ('Relay_Log_Pos',),
        ('Relay_Master_Log_File',),
        ('Slave_IO_Running',),
        ('Slave_SQL_Running',),
        ('Replicate_Do_DB',),
        ('Replicate_Ignore_DB',),
        ('Replicate_Do_Table',),
        ('Replicate_Ignore_Table',),
        ('Replicate_Wild_Do_Table',),
        ('Replicate_Wild_Ignore_Table',),
        ('Last_Errno',),
        ('Last_Error',),
        ('Skip_Counter',),
        ('Exec_Master_Log_Pos',),
        ('Relay_Log_Space',),
        ('Until_Condition',),
        ('Until_Log_File',),
        ('Until_Log_Pos',),
        ('Master_SSL_Allowed',),
        ('Master_SSL_CA_File',),
        ('Master_SSL_CA_Path',),
        ('Master_SSL_Cert',),
        ('Master_SSL_Cipher',),
        ('Master_SSL_Key',),
        ('Seconds_Behind_Master',),
        ('Master_SSL_Verify_Server_Cert',),
        ('Last_IO_Errno',),
        ('Last_IO_Error',),
        ('Last_SQL_Errno',),
        ('Last_SQL_Error',),
    )
    mocker.result(fields)
    cursor.fetchone()
    result = None
    mocker.result(result)
    cursor.close()
    mocker.replay()
    try:
        client = MySQLClient(read_default_file='/etc/my.cnf')
        expected_status = None
        slave_status = client.show_slave_status()
        assert_equals(slave_status, expected_status)
        mocker.verify()
    finally:
        mocker.restore()

def test_status():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    cursor.execute('SHOW GLOBAL STATUS LIKE %s', ('Bytes_sent',))
    cursor.fetchone()
    mocker.result(('Bytes_sent', 978))
    cursor.close()
    mocker.replay()

    try:
        client = MySQLClient()
        assert_equals(client.show_status('Bytes_sent'), 978)
    finally:
        mocker.restore()

def test_variable():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    sql = 'SHOW SESSION VARIABLES LIKE %s'
    cursor.execute(sql, ('sql_log_bin',))
    mocker.result(1)
    cursor.fetchone()
    mocker.result(('sql_log_bin', 'ON'))
    cursor.close()
    mocker.replay()

    try:
        client = MySQLClient()
        assert_equals(client.show_variable('sql_log_bin', session=True), 'ON')
    finally:
        mocker.restore()

def test_variable_nomatch():
    mocker = Mocker()
    connect = mocker.replace('MySQLdb.connect')
    link = connect(ARGS, KWARGS)
    mocker.result(link)
    cursor = link.cursor()
    sql = 'SHOW SESSION VARIABLES LIKE %s'
    cursor.execute(sql, ('postgresql',))
    mocker.result(0)
    cursor.fetchone()
    mocker.result(None)
    cursor.close()
    mocker.replay()

    try:
        client = MySQLClient()
        assert_equals(client.show_variable('postgresql', session=True), None)
    finally:
        mocker.restore()
