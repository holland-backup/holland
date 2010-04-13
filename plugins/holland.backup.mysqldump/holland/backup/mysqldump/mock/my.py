"""Mock various MySQL junk"""
import os
import logging
import MySQLdb
from mocker import *
from hldump.mysql.option import parse_options

def mock_mysql(mocker):
    mock_mysql_config(mocker)
    mock_mysql_option(mocker)
    mock_mysqldb_connect(mocker)
    mock_mysql_client(mocker)

def mock_mysql_client(mocker):
    client_cls = mocker.replace('hldump.mysql.client.MySQLClient')
    client = client_cls(ARGS, KWARGS)
    client.stop_slave()
    mocker.result(None)
    mocker.count(min=0,max=None)
    client.start_slave()
    mocker.result(None)
    mocker.count(min=0,max=None)

def mock_mysql_config(mocker):
    obj = mocker.replace('hldump.core.mysql_config')
    file = obj(ANY)
    mocker.call(lambda x: _mysql_config(mocker, x))

def _mysql_config(mocker, options):
    mysql_keys = ['user','password','host','port','socket']
    mysql_options = { 'client' : dict([(key, value)
                          for key, value in options.items()
                              if key in mysql_keys])
                    }

    if options['defaults_file']:
        defaults_file = os.path.expanduser(options['defaults_file'])
        defaults_file = os.path.abspath(defaults_file)
        logging.info("defaults-file %s", defaults_file)
        my_cnf = parse_options(open(defaults_file, 'r'))
        mysql_options.update(my_cnf)

    mocker.mysql_options = mysql_options
    return 'my.mock.cnf'

def mock_mysql_option(mocker):
    obj = mocker.replace('hldump.mysql.option.write_options')
    obj(ARGS,KWARGS)
    mocker.count(min=0,max=None)

def mock_mysqldb_connect(mocker):
    # What we want to happen is that when we're called with:
    # MySQLdb.connect(read_default_file='my.mock.cnf')
    # instead we run:
    # MySQLdb.connect(user=..., password=..., etc.)
    # once mysql_config is called, we'll have a mysql_config object
    # right on the mocker instance
    obj = mocker.replace('MySQLdb.connect')
    conn = obj(KWARGS, read_default_file=CONTAINS('my.mock.cnf'))
    mocker.count(min=0,max=None)
    mocker.call(lambda *args, **kwargs: _mysqldb_connect(mocker, *args, **kwargs))
   
def _mysqldb_connect(mocker, *args, **kwargs):
    # pull in the options from mocker.mysql_options if they're available or throw an exception
    logging.info("_mysqldb_connect(*%r, **%r)", args, kwargs)
    kwargs = dict(kwargs)

    kwargs.pop('read_default_file', None)
    kwargs.pop('read_default_group', None)

    if not hasattr(mocker, 'mysql_options'):
        mocker.mysql_options = {}
    mocker.mysql_options.setdefault('client', {})
    for key, value in mocker.mysql_options['client'].items():
        if not value:
            continue
        if key not in ('user', 'password', 'host', 'port', 'socket'):
            continue
        if key == 'password':
            key = 'passwd'
        kwargs[key] = value
    print "MySQLdb.connect(**%r)" % kwargs
    return MySQLdb.connect(**kwargs)

if __name__ == '__main__':
    mocker = Mocker()
    mock_mysql(mocker)
