"""Test a backup job"""

import os, sys
import tempfile
from nose.tools import *
from pkg_resources import FileMetadata, Distribution, working_set
from holland.core import Config, load_plugin
from holland.core.backup.job import BackupJob
from holland.core.backup import BackupPlugin, BackupError

# Mock a real plugin without running setup.py
# XXX: Share this code between tests/*/plugin and tests/*/backup/
class MockMetadata(FileMetadata):
    def __init__(self, path):
        self.path = path

    def has_metadata(self, name):
        return name in ('PKG-INFO', 'entry_points.txt')

    def get_metadata(self, name):
        if name == 'PKG-INFO':
            return ''
        if name == 'entry_points.txt':
            # this should be something unlikely to conflict
            # with normal entrypoints elsewhere
            return """
            [holland.backup]
            foo     = backup_plugin:TestBackupPlugin
            """
        raise KeyError("MockMetadata: %s" % name)

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

test_config = Config.parse("""
[holland:backup]
plugin = foo
""".splitlines())

def setup():
    # ensure our backup plugin pkg 'backup_plugin' is importable
    sys.path.append(os.path.dirname(__file__))
    path = os.path.join(os.path.dirname(__file__), 'backup_plugin')
    distribution = Distribution(path, project_name='jobtest',  metadata=MockMetadata(path))
    working_set.add(distribution)

def test_job():
    cfg = Config(test_config)
    BackupPlugin.configspec().validate(cfg)
    store = FakeStore()
    plugin = load_plugin('holland.backup', 'foo')

    job = BackupJob(plugin, cfg, store)
    job.run(dry_run=True)
    assert_equals(plugin.events,
                  ['config', 'setup', 'pre', 'dryrun', 'post'])

    del plugin.events[:]
    job.run(dry_run=False)

def test_job_failure():
    cfg = Config(test_config)
    BackupPlugin.configspec().validate(cfg)
    store = FakeStore()
    plugin = load_plugin('holland.backup', 'foo')
    job = BackupJob(plugin, cfg, store)

    plugin.die_please = True

    assert_raises(BackupError, job.run)

    ok_('post' in plugin.events)
