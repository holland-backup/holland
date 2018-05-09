import os
from holland.backup.lvm.pylvm.objects import *
from nose.tools import *
from .lvm_helper import *

def test_find_lv():
    lv, = LogicalVolume.find('%s/%s' % (VGNAME, LVNAME))
    assert lv.lv_name == LVNAME
    assert lv.volume_group.vg_name == VGNAME
    lv = LogicalVolume.find_one("%s/%s" % (VGNAME, LVNAME))
    assert lv.lv_name == LVNAME
    assert lv.volume_group.vg_name == VGNAME
    assert_raises(LVMError, LogicalVolume.find_one, '%s/foo-bar-baz' % VGNAME)
test_find_lv.setup = lv_setup
test_find_lv.teardown = lv_teardown

def test_lv_is_mounted():
    lv, = LogicalVolume.find('%s/%s' % (VGNAME, LVNAME))
    lv.mount(MOUNTPOINT)
    assert lv.is_mounted() is True
    lv.unmount()
    assert lv.is_mounted() is False
test_lv_is_mounted.setup = lv_setup
test_lv_is_mounted.teardown = lv_teardown

def test_find_vg():
    # find, finds a list
    vg, = VolumeGroup.find(VGNAME)
    assert vg.vg_name == VGNAME
    assert LVNAME in [x.lv_name for x in vg.lvs] 

    # find_one returns first matching
    vg = VolumeGroup.find_one(VGNAME)
    assert vg.vg_name == VGNAME
    assert LVNAME in [x.lv_name for x in vg.lvs]
    
    # Also check that missing groups raise appropriate errors
    assert_raises(LVMError, VolumeGroup.find_one, 'foo-bar-baz')

test_find_vg.setup = lv_setup
test_find_vg.teardown = lv_teardown

def test_lv_str_repr():
    lv, = LogicalVolume.find('%s/%s' % (VGNAME, LVNAME))
    assert str(lv).startswith('LogicalVolume(')
    assert repr(lv) == str(lv)
test_lv_str_repr.setup = lv_setup
test_lv_str_repr.teardown = lv_teardown

def test_vg_str_repr():
    vg, = VolumeGroup.find(VGNAME)
    assert str(vg) == repr(vg)
test_vg_str_repr.setup = lv_setup
test_vg_str_repr.teardown = lv_teardown

def test_lvobj_remove_mounted():
    lv, = LogicalVolume.find('%s/%s' % (VGNAME, LVNAME))
    snapshot = lv.snapshot()
    snapshot.mount(MOUNTPOINT)
    assert_raises(AssertionError, snapshot.remove)
    snapshot.unmount()
    snapshot.remove()
test_lvobj_remove_mounted.setup = lv_setup
test_lvobj_remove_mounted.teardown = lv_teardown

def test_lvobj_remove():
    lv, = LogicalVolume.find('%s/%s' % (VGNAME, LVNAME))
    snapshot_lv = lv.snapshot()
    ok_(snapshot_lv.exists())
    snapshot_lv.remove()
    ok_(not snapshot_lv.exists())

test_lvobj_remove.setup = lv_setup
test_lvobj_remove.teardown = lv_teardown
