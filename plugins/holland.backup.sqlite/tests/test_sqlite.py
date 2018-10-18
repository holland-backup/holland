
import os
import time
import shutil
from tempfile import mkdtemp
from configobj import ConfigObj
from nose.tools import ok_, assert_equals, with_setup

from holland.backup.sqlite import SQLitePlugin
from holland.lib.which import which


class MockConfig(ConfigObj):
    def validate_config(self, *args, **kw):
        pass

config = MockConfig()
config['sqlite'] = {
    'databases' : [os.path.join(os.path.dirname(__file__), 'sqlite.db')]
    }
config['compression'] = {
    'method': 'gzip',
    'inline': 'yes',
    'level': 1
    }

try:
    config['sqlite']['binary'] = which('sqlite')
except Exception:
    config['sqlite']['binary'] = which('sqlite3')


def setup_func():
    "set up test fixtures"
    config['tmpdir'] = mkdtemp()

def teardown_func():
    "tear down test fixtures"
    if os.path.exists(config['tmpdir']):
        shutil.rmtree(config['tmpdir'])

@with_setup(setup_func, teardown_func)
def test_sqlite_dry_run():
    name = 'sqlite/' + time.strftime('%Y%m%d_%H%M%S')
    dry_run = True
    plugin = SQLitePlugin(name, config, config['tmpdir'], dry_run)
    plugin.backup()

@with_setup(setup_func, teardown_func)
def test_sqlite_plugin():
    name = 'sqlite/' + time.strftime('%Y%m%d_%H%M%S')
    dry_run = False
    plugin = SQLitePlugin(name, config, config['tmpdir'], dry_run)
    assert_equals(plugin.estimate_backup_size(), 2048)
    plugin.backup()

@with_setup(setup_func, teardown_func)
def test_sqlite_info():
    name = 'sqlite/' + time.strftime('%Y%m%d_%H%M%S')
    dry_run = False
    plugin = SQLitePlugin(name, config, config['tmpdir'], dry_run)
    ok_(isinstance(plugin.info(), str))

