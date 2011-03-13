"""Test a backup job"""

import os, sys
import shutil
import tempfile
from nose.tools import *
from pkg_resources import FileMetadata, Distribution, working_set
from holland.core import Config, load_plugin
from holland.core.backup import BackupManager, BackupError, BackupSpool

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

test_config = Config.from_string("""
[holland:backup]
plugin = foo
""")

spool = None

def setup():
    # ensure our backup plugin pkg 'backup_plugin' is importable
    sys.path.append(os.path.dirname(__file__))
    path = os.path.join(os.path.dirname(__file__), 'backup_plugin')
    distribution = Distribution(os.path.dirname(path),
                                project_name='mgrtest',
                                metadata=MockMetadata(path))
    working_set.add(distribution)

    global spool
    spool = BackupSpool(tempfile.mkdtemp())

def teardown():
    shutil.rmtree(spool.root)

def test_backup_manager():
    cfg = Config(test_config)
    cfg.name = 'foo'
    mgr = BackupManager(spool.root)

    mgr.backup(cfg)
