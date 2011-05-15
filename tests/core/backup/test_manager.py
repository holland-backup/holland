"""Test a backup job"""

import os, sys
import shutil
import tempfile
from nose.tools import *
from holland.core import Config, load_plugin
from holland.core.backup import BackupManager, BackupError, BackupSpool

test_config = Config.from_string("""
[holland:backup]
plugin = backup-test
""")

spool = None

def setup():
    global spool
    spool = BackupSpool(tempfile.mkdtemp())

def teardown():
    shutil.rmtree(spool.root)

def test_backup_manager():
    cfg = Config(test_config)
    cfg.name = 'foo'
    mgr = BackupManager(spool.root)

    mgr.backup(cfg)
