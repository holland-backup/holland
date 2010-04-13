import locale
from holland.backup.mysqldump.mock.env import MockEnvironment
from holland.backup.mysqldump.core import start

__test__ = False

STD_OPTIONS = {
    'stop_slave' : True,
    'defaults_file' : '~/.my.cnf',
    'extra_options' : '',
    'file_per_database' : False,
    'compression' : None,
    'exclude_tables' : ['mysql.user']
}

mock_env = MockEnvironment()

def setup():
    locale.setlocale(locale.LC_ALL, '')
    mock_env.replace_environment()

def teardown():
    mock_env.restore_environment()

def test_start():
    opts = dict(STD_OPTIONS)
    start(opts)

def test_start_trx():
    opts = dict(STD_OPTIONS)
    opts['include_databases'] = ['employees']
    start(opts)

def test_start_multiple():
    opts = dict(STD_OPTIONS)
    opts['file_per_database'] = True
    start(opts)

def test_start_mysqlauth():
    opts = dict(STD_OPTIONS)
    opts['socket'] = '/var/lib/mysql/mysql.sock'
    start(opts)

def test_start_no_mycnf():
    opts = dict(STD_OPTIONS)
    opts['defaults_file'] = None
    opts['user'] = 'root'
    opts['password'] = None
    opts['socket'] = '/var/lib/mysql/mysql.sock'
    start(opts)

def test_start_exclude_engines():
    opts = dict(STD_OPTIONS)
    opts['exclude_engines'] = ['myisam']
    start(opts)
