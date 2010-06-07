import os
import sys
import logging
from holland.backup.lvm.snapshot import SnapshotLifecycle
from holland.backup.lvm.pylvm import unmount, LVMError, lvremove
from nose.tools import *

# XXX: Setup a LV under ENV[LVM_TEST_VG]
# XXX: Mount LV under ENV[LVM_TEST_MP]
def _test_run():
    fsm = SnapshotLifecycle('/mnt/lvm_test')
    fsm.run()

def test_lvmfsm_misconfigured():
    """Test attempting to snapshot a directory not on an lvm device"""
    fsm = SnapshotLifecycle(target_directory='/home')
    assert_raises(LVMError, fsm.run)

def _test_lv_notfound():
    fsm = SnapshotLifecycle()
    fsm.lvname = 'dba/epicfail' # This LV shouldn't exist
    assert_raises(TypeError, fsm.run)

fileobj = None
def _do_naughty_things(*args):
    global fileobj
    logging.debug("Opening .foo on the mounted snapshot to break unmounting")
    fileobj = open('/tmp/mysnapshot/.foo', 'w')

def _cleanup_naughtiness():
    if not fileobj: return
    fileobj.close()
    unmount('/tmp/mysnapshot')
    lvremove('/dev/vg_test/lv_test_snapshot')

def test_snapshot_error():
    fsm = SnapshotLifecycle(target_directory='/mnt/lvm_test',
                            snapshot_mountpoint='/tmp/mysnapshot/')
    # be naughty and chdir to the snapshot after its mounted
    # this will cause a failure on the unmount phase
    fsm.add_callback('backup', _do_naughty_things)
    assert_raises(LVMError, fsm.run)
test_snapshot_error.teardown = _cleanup_naughtiness

def test_overallocated_snapshot():
    fsm = SnapshotLifecycle(target_directory='/mnt/lvm_test',
                            snapshot_mountpoint='/tmp/mysnapshot/',
                            snapshot_size='768M')
    assert_raises(EnvironmentError, fsm.run)

def test_bad_snapshot_mountpoint():
    fsm = SnapshotLifecycle(target_directory='/mnt/lvm_test',
                            snapshot_mountpoint='/tmp/foo/bar/baz')
    assert_raises(EnvironmentError, fsm.run)

def _do_remount(snapshot):
    snapshot.mount('/tmp/mysnapshot')

def test_bad_remove():
    fsm = SnapshotLifecycle(target_directory='/mnt/lvm_test',
                            snapshot_mountpoint='/tmp/mysnapshot')
    fsm.add_callback('preremove', _do_remount)
    assert_raises(AssertionError, fsm.run)

def test_good_snapshot():
    fsm = SnapshotLifecycle(target_directory='/mnt/lvm_test',
                            snapshot_mountpoint='/tmp/mysnapshot')
    fsm.run()
