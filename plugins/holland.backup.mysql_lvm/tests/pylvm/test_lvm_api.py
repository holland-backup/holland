import os
from holland.backup.lvm.pylvm.api import *
from nose.tools import *
from .lvm_helper import *

def test_pvs():
    for pv in pvs():
        if pv['vg_name'] == VGNAME:
            break
    else:
        pv = None
    assert pv is not None, "Could not find Physical Volume for tested volume group %r" % VGNAME
    pv_again, = pvs(pv['pv_name'])
    ok_(pv_again['pv_name'] == pv['pv_name'])

def test_lvm_dict():
    info = "LVM2_PV_NAME='/dev/sdb' LVM2_VG_NAME='dba' LVM2_PV_FMT='lvm2' LVM2_PV_ATTR='a-' LVM2_PV_SIZE='135.50G' LVM2_PV_FREE='4.50G'"
    dinfo, = lvm_dict(info)
    assert 'pv_name' in dinfo

def test_lvremove():
    lvremove('%s/pylvm_test' % VGNAME)
    assert_raises(LVMError, lvs, '%s/pylvm_test' % VGNAME)
test_lvremove.setup = lv_setup

def test_lvremove_invalid():
    assert_raises(LVMError, lvremove, 'foobarbaz')

def test_lvsnapshot():
    lvsnapshot(lv_name='%s/pylvm_test' % VGNAME,
               snapshot_name='pylvm_test_snapshot',
               snapshot_size='64M')
    lvremove('%s/pylvm_test_snapshot' % VGNAME)
test_lvsnapshot.setup = lv_setup
test_lvsnapshot.teardown = lv_teardown

def test_mount_unmount():
    device_path = os.path.join(os.sep, 'dev', VGNAME, 'pylvm_test')
    pre_mount_dev = os.stat(MOUNTPOINT).st_dev
    mount(device_path, MOUNTPOINT)
    post_mount_dev = os.stat(MOUNTPOINT).st_dev
    ok_(pre_mount_dev != post_mount_dev, "Mount did not change device!")

    pre_unmount_dev = os.stat(MOUNTPOINT).st_dev
    unmount(MOUNTPOINT)
    post_unmount_dev = os.stat(MOUNTPOINT).st_dev
    ok_(pre_mount_dev != post_mount_dev, "Unmount did not change path device!")
test_mount_unmount.setup = lv_setup
test_mount_unmount.teardown = lv_teardown

def test_lv_exists():
    lv_setup()
    device_path = os.path.join(os.sep, 'dev', VGNAME, 'pylvm_test')
    ok_(os.path.exists(device_path), "lvcreate succeeded, but could not find logical volume!")
test_lv_exists.teardown = lv_teardown
