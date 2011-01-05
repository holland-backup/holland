import sys
from nose.tools import *
from holland.lib.lvm.base import *
from holland.lib.lvm.util import getdevice
from tests.constants import *

def test_basevolume():
    assert_raises(NotImplementedError, Volume)

    class Test(Volume):
        pass

    ok_(Test())

    volume = Test({ 'foo' : 'bar', 'baz' : 'biz' })
    assert_equals(volume.foo, 'bar')
    assert_equals(volume.baz, 'biz')
    assert_raises(AttributeError, volume.__getattr__, 'blah')

    assert_raises(NotImplementedError, volume.reload)
    assert_raises(NotImplementedError, Test.lookup, 'foo')
    assert_raises(NotImplementedError, Test.search, 'foo')

    assert_equals(repr(Test()), 'Test()')


class TestPhysicalVolume(object):
    def test_create(self):
        """Test creating a physical volume"""

    def test_reload(self):
        """Test reloading a PhysicalVolume"""
        pv = PhysicalVolume.lookup('/dev/loop0')
        assert_equals(pv.pv_name, '/dev/loop0')
        pv.reload()
        assert_equals(pv.pv_name, '/dev/loop0')

    def test_lookup(self):
        """Test looking up a single physical volume"""
        pv = PhysicalVolume.lookup('/dev/loop0')
        assert_equals(pv.pv_name, '/dev/loop0')

    def test_lookup_failure(self):
        """Test looking up an invalid pv"""
        assert_raises(LookupError, PhysicalVolume.lookup, '/dev/loop1')
        
    def test_search(self):
        """Test searching for a physical volume"""
        # stupid simple test to make sure we're returning an iterable
        # not just a Volume object
        result = PhysicalVolume.search('/dev/loop0')
        ok_(not isinstance(result, Volume))
        pv = result.next()
        ok_(isinstance(pv, PhysicalVolume), "not a physical volume? %r" % pv)
        assert_raises(StopIteration, result.next)

    def test_repr(self):
        pv = PhysicalVolume.lookup('/dev/loop0')
        assert_equals(repr(pv), "PhysicalVolume(device='/dev/loop0')")


class TestVolumeGroup(object):

    def test_create(self):
        vg = VolumeGroup({ 'vg_name' : 'dba', 'vg_extent_size' : 4*1024**2 })
        assert_equals(vg.vg_name, 'dba')
        assert_equals(vg.vg_extent_size, 4194304)

    def test_lookup(self):
        vg = VolumeGroup.lookup("holland")
        assert_equals(vg.vg_name, 'holland')
        assert_equals(vg.lv_count, '1') # only holland/test_lv is created
        assert_equals(vg.pv_count, '1') # only /dev/loopN is assigned

    def test_failing_lookup(self):
        assert_raises(LookupError, VolumeGroup.lookup, 'holland_missing')

    def test_search(self):
        for vg in VolumeGroup.search('holland'):
            assert_equals(vg.vg_name, 'holland')
            assert_equals(vg.lv_count, '1') # only holland/test_lv is created
            assert_equals(vg.pv_count, '1') # only /dev/loopN is assigned

    def test_reload(self):
        # XXX: not sure a good way to check this - do something to change the vg
        vg = VolumeGroup.lookup('holland')
        vg.reload()
        assert_equals(vg.vg_name, 'holland')

    def test_repr(self):
        vg = VolumeGroup.lookup('holland')
        assert_equals(repr(vg), 'VolumeGroup(vg_name=holland)')

class TestLogicalVolume(object):
    def test_create(self):
        """Test creating a LogicalVolume"""
        lv = LogicalVolume({ 'lv_name' : 'mysql', 'vg_name' : 'dba' })
        assert_equals(lv.lv_name, 'mysql')

    def test_happy_lookup(self):
        """Test a loading an existing lv"""
        lv = LogicalVolume.lookup('holland/test_lv')
        assert_equals(lv.vg_name, 'holland')
        assert_equals(lv.lv_name, 'test_lv')

    def test_sad_lookup(self):
        assert_raises(LookupError, LogicalVolume.lookup, 'holland/test_lv_missing')

    def test_look_from_fspath(self):
        lv = LogicalVolume.lookup_from_fspath(MNT_DIR)
        assert_equals(lv.vg_name, TEST_VG)
        assert_equals(lv.lv_name, TEST_LV)

    def test_search(self):
        for lv in LogicalVolume.search('%s/%s' % (TEST_VG, TEST_LV)):
            assert_equals(lv.vg_name, TEST_VG)
            assert_equals(lv.lv_name, TEST_LV)

    def test_reload(self):
        # XXX: need to test changing attributes and reloading
        lv = LogicalVolume.lookup(TEST_VG)
        lv.reload()
        assert_equals(lv.lv_name, TEST_LV)

    def test_snapshot(self):
        lv = LogicalVolume.lookup('%s/%s' % (TEST_VG, TEST_LV))
        snapshot = None
        try:
            snapshot = lv.snapshot(lv.lv_name + '_snapshot', 1)
            ok_(lv != snapshot)
            ok_('s' in snapshot.lv_attr)
            assert_equals(snapshot.lv_size, snapshot.vg_extent_size)
            snapshot.mount(MNT_DIR, options='nouuid')
            ok_(snapshot.is_mounted())
            assert_equals(getdevice(MNT_DIR), os.path.realpath(snapshot.device_name()))
            lv.reload()
            snapshot.unmount()
            assert_equals(snapshot.is_mounted(), False)
            snapshot.remove()
            ok_(not snapshot.exists())
            snapshot = None
        finally:
            if snapshot and snapshot.is_mounted():
                snapshot.unmount()
            if snapshot and snapshot.exists():
                snapshot.remove()

    def test_filesystem(self):
        """Test looking up filesystem of lv"""
        lv = LogicalVolume.lookup('holland/test_lv')
        assert_equals(lv.filesystem(), 'xfs')

    def test_bad_filesystem(self):
        """Test looking for filesystem of a lv that doesn't exist"""
        lv = LogicalVolume()
        lv.vg_name = 'holland'
        lv.lv_name = 'test_lv_missing' # <- doesn't exist in our setup
        assert_raises(LookupError, lv.filesystem)

    def test_volume_group(self):
        lv = LogicalVolume.lookup('%s/%s' % (TEST_VG, TEST_LV))
        vg = lv.volume_group()
        assert_equals(vg.vg_name, lv.vg_name)
        assert_equals(vg.vg_extent_size, lv.vg_extent_size)

    def test_repr(self):
        lv = LogicalVolume.lookup('holland/test_lv')
        assert_equals(repr(lv), 'LogicalVolume(device=\'/dev/holland/test_lv\')')
