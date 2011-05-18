import shutil
from nose.tools import *
from tempfile import mkdtemp

from holland.lib.mysql.cli import MyCmdParser

global tmpdir

def setup_func():
    global tmpdir
    tmpdir = mkdtemp()

def teardown_func():
    global tmpdir
    shutil.rmtree(tmpdir)

@with_setup(setup_func, teardown_func)
def test_mysqlcmdparser():
    global tmpdir

    cli = MyCmdParser('mysqldump')
    ok_(isinstance(cli.cli_version, tuple))
    ok_(cli.cli_options)
    ok_(cli.cli_defaults)
    ok_(cli.has_key('opt'))
    ok_(cli.has_key('single-transaction'))

@raises(IOError)
@with_setup(setup_func, teardown_func)
def test_mysqlcmdparser_bad_command():
    global tmpdir

    cli = MyCmdParser('_doesnt_exist_mysqldumb')
    ok_(isinstance(cli.cli_version, tuple))

@with_setup(setup_func, teardown_func)
def test_parse_mysqld():
    global tmpdir

    cli = MyCmdParser('/usr/libexec/mysqld')
    ok_(isinstance(cli.cli_version, tuple))
    ok_(cli.cli_options)
    ok_(cli.cli_defaults)
    ok_(cli.has_key('log-bin'))
    ok_(cli.has_key('binlog-do-db'))
