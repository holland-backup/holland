"""
Test behavior of MySQLClient class
"""

__test__ = True

from MySQLdb import OperationalError, ProgrammingError
from tempfile import mkdtemp
import shutil
from nose.tools import *
from holland.lib.mysql.client.legacy import MySQLClient

global tmpdir, client

def setup_func():
    global tmpdir, client
    client = MySQLClient(read_default_group='client')
    tmpdir = mkdtemp()

def teardown_func():
    global tmpdir, client
    shutil.rmtree(tmpdir)

@with_setup(setup_func, teardown_func)
def test_quoting():
    global tmpdir, client
    names = ['test','bar`foo', 'column']
    eq_(client.quote_id(*names), "`test`.`bar``foo`.`column`")
    names = ["'test'","'bar`foo'", "'column'"]
    eq_(client.unquote_id(*names), ['test','bar`foo', 'column'])
    assert_not_equal(client.unquote_id(*names), names)
    strings = ['a', '\'b', 'c']
    eq_(client.quote(*strings), "'a','''b','c'")

@with_setup(setup_func, teardown_func)
def test_show_databases():
    global tmpdir, client
    res = client.show_databases()
    ok_('mysql' in res)

@with_setup(setup_func, teardown_func)
def test_show_tables():
    global tmpdir, client
    res = client.show_tables('mysql')
    # verify common mysql.XXX tables
    for table in ['user', 'db', 'columns_priv', 'host']:
        ok_(table in res)

@with_setup(setup_func, teardown_func)
def test_show_databases():
    global tmpdir, client
    res = client.show_table_status('mysql')
    for r in res:
        ok_(r.has_key('engine'))

@with_setup(setup_func, teardown_func)
def test_show_variables():
    global tmpdir, client
    res = client.show_variable('port')
    ok_(res == '3306')

@with_setup(setup_func, teardown_func)
def test_show_variable_bad():
    global tmpdir, client
    res = client.show_variable('portsafasfasdfasdffa')
    ok_(res == None)

@with_setup(setup_func, teardown_func)
def test_show_variables_like():
    global tmpdir, client
    res = client.show_variables_like('%version%')
    ok_(res.has_key('version'))
    ok_(res.has_key('protocol_version'))
    ok_(res.has_key('version_compile_machine'))

@with_setup(setup_func, teardown_func)
def test_set_variable():
    global tmpdir, client
    cur_max = int(client.show_variable('max_connections'))
    res = client.set_variable('max_connections', cur_max+10, session=False)
    new_max = client.show_variable('max_connections')
    ok_(cur_max+10 == int(new_max))

@raises(OperationalError)
@with_setup(setup_func, teardown_func)
def test_set_variable_wrong_scope():
    global tmpdir, client
    # max_connections is global variable...  setting session=True raises
    res = client.set_variable('max_connections', 100, session=True)

@raises(OperationalError)
@with_setup(setup_func, teardown_func)
def test_set_variable_bad_variable():
    global tmpdir, client
    res = client.set_variable('johnny_bad_var', 100, session=True)

@with_setup(setup_func, teardown_func)
def test_set_wait_timeout():
    global tmpdir, client
    cur_wait = int(client.show_variable('interactive_timeout'))
    res = client.set_variable('interactive_timeout', cur_wait+10, session=True)
    new_wait = client.show_variable('interactive_timeout', session_only=True)
    ok_(cur_wait+10 == int(new_wait))

@with_setup(setup_func, teardown_func)
def test_show_indexes():
    global tmpdir, client
    res = client.show_indexes('mysql', 'user')
    ok_(type(res) is dict)

@raises(ProgrammingError)
@with_setup(setup_func, teardown_func)
def test_show_indexes_bad_database():
    global tmpdir, client
    res = client.show_indexes('_bad_database_not_exist', 'user')
    ok_(type(res) is dict)

@with_setup(setup_func, teardown_func)
def test_flush_logs():
    global tmpdir, client
    res = client.flush_logs()

@with_setup(setup_func, teardown_func)
def test_flush_tables():
    global tmpdir, client
    # flush all
    client.flush_tables()
    # flush some
    client.flush_tables(table_list=['mysql.user', 'mysql.column_priv'])

@with_setup(setup_func, teardown_func)
def test_flush_tables_bad():
    global tmpdir, client
    # flush something that doesn't exist, doesn't raise anything
    client.flush_tables(table_list=['mysql_bad.user', 'mysql_bad.column_priv'])

@with_setup(setup_func, teardown_func)
def test_flush_tables_with_read_lock():
    global tmpdir, client
    client.flush_tables_with_read_lock()
    client.flush_tables_with_read_lock(extra_flush=True)

@with_setup(setup_func, teardown_func)
def test_lock_tables():
    global tmpdir, client
    client.lock_tables(table_list=['mysql.user', 'mysql.columns_priv'])

@with_setup(setup_func, teardown_func)
def test_unlock_tables():
    global tmpdir, client
    client.unlock_tables()

@with_setup(setup_func, teardown_func)
def test_walk_databases():
    global tmpdir, client
    for db in client.walk_databases():
        ok_(len(db) > 0)

@with_setup(setup_func, teardown_func)
def test_walk_tables():
    global tmpdir, client
    for table in client.walk_tables():
        ok_(type(table) == dict)

    for table in client.walk_tables(dbinclude=['mysql']):
        ok_(type(table) == dict)

@with_setup(setup_func, teardown_func)
def test_walk_tables_bad_db():
    global tmpdir, client

    for table in client.walk_tables(dbinclude=['Johnny_not_exist_mysql']):
        ok_(type(table) == dict)

@with_setup(setup_func, teardown_func)
def test_master_status():
    # FIXME: Need a master to be setup to get info on it
    global tmpdir, client
    res = client.show_master_status()

@with_setup(setup_func, teardown_func)
def test_slave_status():
    # FIXME: Need a slave to be setup to get info on it
    global tmpdir, client
    res = client.show_slave_status()

@with_setup(setup_func, teardown_func)
def test_is_slave_running():
    # FIXME: Need a slave to be setup
    global tmpdir, client
    res = client.is_slave_running()
    eq_(res, False)

@raises(OperationalError)
@with_setup(setup_func, teardown_func)
def test_start_slave():
    # FIXME: Need a slave to be setup
    global tmpdir, client
    res = client.start_slave()

@raises(OperationalError)
@with_setup(setup_func, teardown_func)
def test_stop_slave():
    # FIXME: Need a slave to be setup
    global tmpdir, client
    res = client.stop_slave()

@with_setup(setup_func, teardown_func)
def test_show_transactional_engines():
    global tmpdir, client
    res = client.show_transactional_engines()
    ok_('innodb' in res)

@with_setup(setup_func, teardown_func)
def test_server_version():
    global tmpdir, client
    res = client.server_version()
    ok_(type(int(res[0])) is int)
    ok_(type(int(res[1])) is int)
    ok_(type(int(res[2])) is int)

@with_setup(setup_func, teardown_func)
def test_is_transactional():
    global tmpdir, client
    res = client.is_transactional('innodb')
    eq_(res, True)
    res = client.is_transactional('myisam')
    eq_(res, False)
    res = client.is_transactional('johnny_engine_not_exist')
    eq_(res, False)

@with_setup(setup_func, teardown_func)
def test_encode_as_filename():
    global tmpdir, client
    if client.server_version() < (5, 1, 2):
        # This should throw an OperationalError
        try:
            res = client.encode_as_filename('latin')
            ok_(False)
        except OperationalError, e:
            ok_(True)
    else:
        res = client.encode_as_filename('latin')
        ok_(res)

@with_setup(setup_func, teardown_func)
def test_show_encoded_dbs():
    global tmpdir, client
    if client.server_version() < (5, 1, 2):
        # This should throw an OperationalError
        try:
            res = client.show_encoded_dbs()
            ok_(False)
        except OperationalError, e:
            ok_(True)
    else:
        res = client.show_encoded_dbs()
        ok_(type(res) == list)
