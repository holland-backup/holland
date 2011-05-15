"""Test a backup job"""

import os, sys
import shutil
import tempfile
from nose.tools import *
from holland.core import Config, load_plugin
from holland.core.backup.job import BackupJob
from holland.core.backup.spool import BackupStore
from holland.core.backup import BackupPlugin, BackupError

test_config = Config.from_string("""
[holland:backup]
plugin = backup-test
""")

tmpdir = None

def setup():
    global tmpdir
    tmpdir = tempfile.mkdtemp()

def teardown():
    if tmpdir is not None:
        try:
            shutil.rmtree(tmpdir)
        except OSError:
            pass

def test_job():
    cfg = Config(test_config)
    BackupPlugin.configspec().validate(cfg)
    store = BackupStore('stub', tmpdir)
    plugin = load_plugin('holland.backup', 'backup-test')

    job = BackupJob(plugin, cfg, store)
    job.run(dry_run=True)
    assert_equals(plugin.events,
                  ['config', 'setup', 'pre', 'dryrun', 'post'])

    del plugin.events[:]
    job.run(dry_run=False)

def test_job_failure():
    cfg = Config(test_config)
    BackupPlugin.configspec().validate(cfg)
    store = BackupStore('stub', tmpdir)
    plugin = load_plugin('holland.backup', 'backup-test')
    job = BackupJob(plugin, cfg, store)

    plugin.die_please = True

    assert_raises(BackupError, job.run)

    ok_('post' in plugin.events)
