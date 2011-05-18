import os, sys
import shutil
import tempfile
import subprocess
from nose.tools import *
from holland.lib.lvm.raw import *
from tests.constants import *

__test__ = False

def test_pvs():
    pvs(LOOP_DEV)

def test_vgs():
    vg, = vgs(TEST_VG)
    assert_equals(vg['vg_name'], TEST_VG)
    assert_equals(int(vg['pv_count']), 1)

def test_lvs():
    lv, = lvs('%s/%s' % (TEST_VG,TEST_LV))
    assert_equals(lv['vg_name'], TEST_VG)
    vg_extents = int(lv['vg_extent_count'])
    vg_extent_size = int(lv['vg_extent_size'])

    assert_equals(int(lv['lv_size']), IMG_SIZE / 2)

def ensure_snapshot_unmount():
    try:
        umount('/dev/%s/%s_snapshot' % (TEST_VG, TEST_LV))
    except:
        pass

def test_snapshot():
    lvsnapshot('%s/%s' % (TEST_VG, TEST_LV), '%s_snapshot' % TEST_LV , 4, '512K')
    assert_raises(LVMCommandError, lvsnapshot, '%s/%s' % (TEST_VG, TEST_LV), '%s_snapshot' % TEST_LV , 1)
    mount('/dev/%s/%s' % (TEST_VG, TEST_LV), '/mnt/tmp', options='noatime', vfstype='ext3')
    umount('/dev/%s/%s' % (TEST_VG, TEST_LV))
    lvremove('%s/%s_snapshot' % (TEST_VG, TEST_LV))
    assert_raises(LVMCommandError, lvremove, '%s/%s_snapshot' % (TEST_VG, TEST_LV)) # this should fail the 2nd time
test_snapshot.teardown = ensure_snapshot_unmount()

def test_blkid():
    info, = blkid('/dev/%s/%s' % (TEST_VG, TEST_LV))
    assert_equals(info['type'], 'ext3')

def test_bad_mount():
    assert_raises(LVMCommandError, mount, '/dev/%s/%s' % (TEST_VG, TEST_LV), os.path.join(MNT_DIR, 'missing'))
