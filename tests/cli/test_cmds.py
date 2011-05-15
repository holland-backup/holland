
import os
import argparse
import tempfile
import shutil
from nose.tools import with_setup, ok_, eq_
from holland.core.config import Config
from holland.core import BackupManager
from holland.cli.cmd.base import BaseCommand, ArgparseCommand
from holland.cli.cmd.builtin.cmd_backup import Backup
from holland.cli import main

global tmpdir

def startup():
    global tmpdir
    tmpdir = tempfile.mkdtemp()

def teardown():
    global tmpdir
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    
            
def test_cmd_base_command():
    base1 = BaseCommand('test-command')
    base2 = BaseCommand('test-command')
    base3 = BaseCommand('some-other-command')
    
    # added for coverage
    eq_(base1, base2)
    
    res = base1 != base3
    ok_(res)
    
def test_argparse_command():
    # for coverage
    a = ArgparseCommand('test')
    eq_(a.__call__(args=None), 1)

@with_setup(startup, teardown)
def test_cmd_backup():
    global tmpdir
    backup = Backup('test')
    config = Config()
    config['holland'] = Config()
    config['holland']['backup-directory'] = tempfile.mkdtemp()
    config['holland']['backupsets'] = []
    backup.configure(config)
    parser = backup.create_parser()
    ns = argparse.Namespace(directory=None, backupset=['test'])
    
    shutil.rmtree(tmpdir)
    
    # cause error condition because namespace.directory is None
    eq_(backup.execute(ns, parser), 1)
    
    backup.run_backup('default', BackupManager(tmpdir), 
                    skip_hooks=True, 
                    dry_run=True) 