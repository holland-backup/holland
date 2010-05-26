import os, sys
import shutil
import tempfile
import subprocess
from nose.tools import *
from holland.lib.lvm.raw import *

LOOP_DEV = '/dev/loop0'
IMG_FILE = '/tmp/hl_lvm.img'
IMG_SIZE = 128*1024**2
TEST_VG = 'holland'
TEST_LV = 'test_lv'
MNT_DIR = tempfile.mkdtemp()

def setup():
    """Setup a simple LVM device to use"""
    os.environ['PATH'] = '/sbin:/usr/sbin:' + os.environ['PATH']
    size = IMG_SIZE / 512
    img_path = os.path.join(MNT_DIR, 'test.img')
    subprocess.call("dd if=/dev/zero of=%s count=%d" % 
                    (img_path, size), shell=True)
    subprocess.call("losetup %s %s" % (LOOP_DEV, img_path), shell=True)
    subprocess.call("pvcreate %s" % LOOP_DEV, shell=True)
    subprocess.call("vgcreate %s %s" % 
                    (TEST_VG, LOOP_DEV), shell=True)
    subprocess.call("lvcreate -L%dK -n %s %s" %
                    ((IMG_SIZE / 2) / 1024, TEST_LV, TEST_VG), shell=True)
    subprocess.call("mkfs.ext3 /dev/%s/%s" % 
                    (TEST_VG, TEST_LV), shell=True)
    subprocess.call("mount /dev/%s/%s %s" %
                    (TEST_VG, TEST_LV, MNT_DIR), shell=True)
    # dd if=/dev/zero of=$staging/foo.img count=N
    # losetup /dev/loopN $staging/foo.img
    # pvcreate /dev/loopN
    # vgcreate $test_vg /dev/loopN
    # lvcreate $test_lv
    # mkfs /dev/$test_vg/$test_lv 
    # mount /dev/$test_vg/$test_lv somepath


def teardown():
    """Remove the previously setup LVM"""
    subprocess.call("umount %s" % MNT_DIR, shell=True)
    subprocess.call("vgremove -f %s" % TEST_VG, shell=True)
    subprocess.call('losetup -d %s' % LOOP_DEV, shell=True)
    shutil.rmtree(MNT_DIR)


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
    # def lvsnapshot(orig_lv_path, snapshot_name, snapshot_extents, chunksize=None):
    lvsnapshot('%s/%s' % (TEST_VG, TEST_LV), '%s_snapshot' % TEST_LV , 4, '512K')
    mount('/dev/%s/%s' % (TEST_VG, TEST_LV), '/mnt/tmp')
    umount('/dev/%s/%s' % (TEST_VG, TEST_LV))
    lvremove('%s/%s_snapshot' % (TEST_VG, TEST_LV))
test_snapshot.teardown = ensure_snapshot_unmount()

def test_blkid():
    info, = blkid('/dev/%s/%s' % (TEST_VG, TEST_LV))
    assert_equals(info['type'], 'ext3')
