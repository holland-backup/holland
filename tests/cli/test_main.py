import os, sys
import subprocess
import shutil
import tempfile
from holland.core import Config
from holland.cli import main
from nose.tools import *

print >>sys.stderr, sys.executable

# tedious setup to make sure this works with our plugins
# mkdtemp staging_dir
# make holland, virtualenv subdirs
# install holland core into virtualenv

def setup():
    global staging_dir
    staging_dir = tempfile.mkdtemp()
    os.mkdir(os.path.join(staging_dir, 'tmp'))
    os.mkdir(os.path.join(staging_dir, 'backups'))
    os.makedirs(os.path.join(staging_dir, 'holland', 'backupsets'))
    os.makedirs(os.path.join(staging_dir, 'holland', 'providers'))

    cfg = Config()
    cfg['holland'] = Config()
    cfg['holland']['backup-directory'] = os.path.join(staging_dir, 'backups')
    cfg['holland']['tmpdir'] = os.path.join(staging_dir, 'tmp')
    cfg['holland']['path'] = os.environ['PATH']
    cfg['logging'] = Config()
    cfg['logging']['level'] = 'info'

    cfg.write(os.path.join(staging_dir, 'holland', 'holland.conf'))

def teardown():
    global staging_dir
    shutil.rmtree(staging_dir)

def holland_config():
    global staging_dir
    return os.path.join(staging_dir, 'holland', 'holland.conf')

def test_holland_main():
    # ensure holland at least runs
    ret = main.holland(['-c', holland_config(), '--log-level', 'debug'])
    # this should return with non-zero status
    assert_equals(ret, 0)

def test_help():
    ret = main.holland(['--help'])
    assert_equals(ret, 1)

    ret = main.holland(['help', 'backup'])
    assert_equals(ret, 0)

    ret = main.holland(['help', 'does-not-exist'])
    ok_(ret != 0)

def test_list_commands():
    ret = main.holland(['list-commands'])
    assert_equals(ret, 0)

def test_list_backups():
    print >>sys.stderr, "holland list-backups"
    ret = main.holland(['-c', holland_config(), 'list-backups'])
    assert_equals(ret, 0)

def test_list_plugins():
    ret = main.holland(['list-plugins'])
    assert_equals(ret, 0)

def test_mkconfig():
    ret = main.holland(['mk-config', 'mysqldump', '--file',
        os.path.join(staging_dir, 'holland', 'backupsets', 'mybackup.conf')])
    assert_equals(ret, 0)
    Config.read([os.path.join(
                    staging_dir,
                    'holland',
                    'backupsets',
                    'mybackup.conf'
                 )
                ])
def test_holland_backup():
    # first with no backupsets - this should fail
    ret = main.holland(['-c', holland_config(), 'backup', '-d', os.path.join(staging_dir, 'backups')])
    ok_(ret != 0)

    ret = main.holland(['-c', holland_config(), 'backup', 'default'])
    ok_(ret != 0)
