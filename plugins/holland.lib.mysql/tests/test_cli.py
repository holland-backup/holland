import shutil
from nose.tools import *
from tempfile import mkdtemp
from subprocess import call, STDOUT
from holland.lib.mysql.cli import MyCmdParser

mysqld = None

def setup():
    global mysqld

    for name in ('/usr/sbin/mysqld', '/usr/libexec/mysqld'):
        try:
            call([name, '--no-defaults', '--user=mysql', '--help'],
                 stdout=open('/dev/null', 'w'),
                 stderr=STDOUT,
                 close_fds=True)
            mysqld = name
        except OSError:
            continue

def test_mysqlcmdparser():
    cli = MyCmdParser('mysqldump')
    ok_(isinstance(cli.cli_version, tuple))
    ok_(cli.cli_options)
    ok_(cli.cli_defaults)
    ok_(cli.has_key('opt'))
    ok_(cli.has_key('single-transaction'))

def test_mysqlcmdparser_bad_command():
    assert_raises(IOError, MyCmdParser, '_doesnt_exist_mysqldumb')

def test_parse_mysqld():
    cli = MyCmdParser(mysqld)
    ok_(isinstance(cli.cli_version, tuple))
    ok_(cli.cli_options)
    ok_(cli.cli_defaults)
    ok_(cli.has_key('log-bin'))
    ok_(cli.has_key('binlog-do-db'))
