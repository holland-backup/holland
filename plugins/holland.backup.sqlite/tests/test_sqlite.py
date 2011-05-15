
import os
import time
import shutil
import tempfile
import copy
from nose.tools import ok_, assert_equals, with_setup, raises

from holland.core import load_plugin, BackupError
from holland.core.config import Config, Configspec
from holland.core.backup.job import BackupJob
from holland.backup.sqlite import SQLitePlugin
from holland.lib.which import which, WhichError


try:
    binary = which('sqlite')    
except WhichError, e:
    try:
        binary = which('sqlite3')
    except WhichError, e:
        raise Exception, "Unable to find sqlite binary"

database = os.path.join(os.path.dirname(__file__), 'example.db')        

spec = Configspec.from_string("""
[holland:backup]
plugin = string

backups-to-keep = integer
auto-purge-failures = string
purge-policy = string
estimated-size-factor = float
estimation-method = string
retention-count = integer

[sqlite]
databases = string
binary = string

[compression]
method = string
inline = string
level = integer
""")

test_config = Config.from_string("""
[holland:backup]
plugin = sqlite

backups-to-keep = 1
auto-purge-failures = yes
purge-policy = after-backup
estimated-size-factor = 1.0
estimation-method = plugin
retention-count = 1

[sqlite]
databases = 
binary = %s

[compression]
method = gzip
inline = yes
level = 1

""" % binary)

test_config = spec.validate(test_config)
test_config['holland:backup']['hooks'] = []
test_config['sqlite']['databases'] = ['', database,]
test_config['hooks'] = None


class MockConfig(Config):
    def validate_config(self, *args, **kw):
        pass
    
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
def test_sqlite_dry_run():
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)
    
    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=True)

@raises(BackupError)
@with_setup(setup_func, teardown_func)    
def test_sqlite_bad_binary():
    plugin = load_plugin('holland.backup', 'sqlite')
    new_config = copy.deepcopy(test_config)
    new_config['sqlite']['binary'] = '/usr/bin/sqlite-doesnt-exist'
    plugin.configure(new_config)
    job = BackupJob(plugin, new_config, FakeStore())
    job.run(dry_run=True)

@with_setup(setup_func, teardown_func)    
def test_sqlite_bad_databases():
    try:
        plugin = load_plugin('holland.backup', 'sqlite')
        new_config = copy.deepcopy(test_config)
        new_config['sqlite']['databases'] = ['', '/path/to/some/bogus/db']
        plugin.configure(new_config)
        plugin.pre()
        plugin.estimate()
        job = BackupJob(plugin, new_config, FakeStore())
        job.run(dry_run=False)
    except BackupError, e:
        pass
        
    try:
        new_config = copy.deepcopy(test_config)
        new_config['sqlite']['databases'] = [database, '/path/to/some/bogus/db']
        plugin.configure(new_config)
        plugin.pre()
        plugin.estimate()
        job = BackupJob(plugin, new_config, FakeStore())
        job.run(dry_run=False)
    except BackupError, e:
        pass
        
@raises(BackupError)
@with_setup(setup_func, teardown_func)    
def test_sqlite_no_databases():
    plugin = load_plugin('holland.backup', 'sqlite')
    new_config = copy.deepcopy(test_config)
    new_config['sqlite']['databases'] = []
    plugin.configure(new_config)
    job = BackupJob(plugin, new_config, FakeStore())
    job.run(dry_run=False)
    
@with_setup(setup_func, teardown_func)
def test_sqlite_estimate():
    dry_run = False
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)
    plugin.pre()
    assert_equals(plugin.estimate(), 2048)
    
@with_setup(setup_func, teardown_func)
def test_sqlite_backup():
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)
    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=False)

@with_setup(setup_func, teardown_func)
def test_sqlite_bad_backup():
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)    
    job = BackupJob(plugin, test_config, FakeStore())
    job.run(dry_run=False)
    job.plugin.config['sqlite']['binary'] = '/usr/bin/false'
    try:
        job.run()
    except IOError, e:
        pass

@with_setup(setup_func, teardown_func)
def test_sqlite_configspec():
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)    
    ok_(plugin.configspec())
    
@with_setup(setup_func, teardown_func)
def test_sqlite_info():
    dry_run = False
    plugin = load_plugin('holland.backup', 'sqlite')
    plugin.configure(test_config)
    plugin.pre()
    ok_(isinstance(plugin.plugin_info(), dict))
    