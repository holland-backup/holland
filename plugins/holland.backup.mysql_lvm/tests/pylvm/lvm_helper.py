"""Help setup lvm volumes"""
import os
from holland.backup.lvm.pylvm.api import lvcreate, lvremove, run_cmd

VGNAME = os.environ['VGNAME']
LVNAME = 'pylvm_test'
LVSIZE = '64M'
MKFS = os.getenv('MKFS', '/sbin/mkfs.ext3')

DEVICE = os.path.join(os.sep, 'dev', VGNAME, LVNAME)

def lv_setup():
    lvcreate(LVNAME, LVSIZE, VGNAME)
    run_cmd(MKFS, DEVICE)

def lv_teardown():
    lvremove(DEVICE)


MOUNTPOINT = None

def setup():
    global MOUNTPOINT
    import tempfile
    MOUNTPOINT = tempfile.mkdtemp()

def teardown():
    if os.path.exists(MOUNTPOINT or ''):
        import shutil
        shutil.rmtree(MOUNTPOINT)

setup()
