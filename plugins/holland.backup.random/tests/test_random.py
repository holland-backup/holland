
import os
import time
import shutil
import tempfile
import copy
from nose.tools import ok_, eq_, assert_equals, with_setup, raises

from holland.core import load_plugin, BackupError
from holland.core.config import Config, Configspec
from holland.core.backup.job import BackupJob
from holland.backup.random import RandomPlugin
from holland.lib.which import which, WhichError

spec = Configspec.from_string("""
[holland:backup]
plugin = string

backups-to-keep = integer
auto-purge-failures = string
purge-policy = string
estimated-size-factor = float
estimation-method = string
retention-count = integer

[random]
bytes = integer

""")

test_config = Config.from_string("""
[holland:backup]
plugin = random

backups-to-keep = 1
auto-purge-failures = yes
purge-policy = after-backup
estimated-size-factor = 1.0
estimation-method = plugin
retention-count = 1

[random]
bytes = 2048

""")

test_config = spec.validate(test_config)
test_config['holland:backup']['hooks'] = []

class FakeSpool(object):
    def __init__(self, backups):
        self.backups = backups


    def purge(self, name, retention_count):
        for backup in self.backups:
            backup.purge()

        return [], [], self.backups
        
class FakeStore(object):
    name = 'fake'

    def __init__(self):
        self.purged = False
        self.path = tempfile.mkdtemp()
        self.spool = FakeSpool([self])

    def oldest(self, n=1):
        return []

    def spool_capacity(self):
        return 32*1024**2

    def size(self):
        return 0

    def purge(self):
        "Fake purge"
        import shutil
        shutil.rmtree(self.path)
        self.purged = True
    
def setup_func():
    "set up test fixtures"
    test_config['tmpdir'] = tempfile.mkdtemp()

def teardown_func():
    "tear down test fixtures"
    if os.path.exists(test_config['tmpdir']):
        shutil.rmtree(test_config['tmpdir'])
    
@with_setup(setup_func, teardown_func)    
def test_random_dry_run():
    plugin = load_plugin('holland.backup', 'random')
    #plugin.configure(test_config)
    
    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=True)

@with_setup(setup_func, teardown_func)    
def test_random_backup():
    plugin = load_plugin('holland.backup', 'random')
    plugin.configure(test_config)
    ok_(plugin.configspec())
    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=False)

@raises(BackupError)
@with_setup(setup_func, teardown_func)    
def test_random_backup_bad_directory():
    plugin = load_plugin('holland.backup', 'random')
    plugin.configure(test_config)

    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=True)
    job.plugin.backup_directory = '/path/to/some/bogus/dir'
    job.plugin.backup()
    
@with_setup(setup_func, teardown_func)    
def test_random_configspec():
    plugin = load_plugin('holland.backup', 'random')
    plugin.configure(test_config)
    ok_(plugin.configspec())

@with_setup(setup_func, teardown_func)    
def test_random_plugin_info():
    plugin = load_plugin('holland.backup', 'random')
    plugin.configure(test_config)
    eq_(plugin.plugin_info().get('name', None), 'random')
