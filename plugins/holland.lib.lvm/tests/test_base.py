import sys
from nose.tools import *
from mocker import Mocker, MATCH
from holland.lib.lvm.base import *

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
    mocker = Mocker()

    def setup_class(cls):
        pvs = cls.mocker.replace('holland.lib.lvm.raw.pvs')
        pvs('/dev/foo1')
        cls.mocker.count(min=10)
        cls.mocker.result([{ 'pv_name' : '/dev/foo1' }])
        pvs(MATCH(lambda x: x != '/dev/foo1'))
        cls.mocker.count(min=1)
        cls.mocker.result([])
        cls.mocker.replay()
    setup_class = classmethod(setup_class)

    def teardown_class(cls):
        cls.mocker.restore()
    teardown_class = classmethod(teardown_class)

    def test_create(self):
        """Test creating a physical volume"""

    def test_reload(self):
        """Test reloading a PhysicalVolume"""
        pv = PhysicalVolume.lookup('/dev/foo1')
        assert_equals(pv.pv_name, '/dev/foo1')
        pv.reload()
        assert_equals(pv.pv_name, '/dev/foo1')

    def test_lookup(self):
        """Test looking up a single physical volume"""
        pv = PhysicalVolume.lookup('/dev/foo1')
        assert_equals(pv.pv_name, '/dev/foo1')

    def test_lookup_failure(self):
        """Test looking up an invalid pv"""
        assert_raises(LookupError, PhysicalVolume.lookup, '/dev/bar5')
        
    def test_search(self):
        """Test searching for a physical volume"""
        # stupid simple test to make sure we're returning an iterable
        # not just a Volume object
        result = PhysicalVolume.search('/dev/foo1')
        ok_(not isinstance(result, Volume))
        pv = result.next()
        ok_(isinstance(pv, PhysicalVolume), "not a physical volume? %r" % pv)

    def test_repr(self):
        pv = PhysicalVolume.lookup('/dev/foo1')
        assert_equals(repr(pv), "PhysicalVolume(device='/dev/foo1')")


class TestLogicalVolume(object):
    mocker = Mocker()

    def setup_class(cls):
        lvs = cls.mocker.replace('holland.lib.lvm.raw.lvs')
        lvs(MATCH(lambda pathspec: pathspec.endswith('dba/mysql') or \
                                   pathspec.endswith('mappper/dba-mysql')))
        cls.mocker.count(min=3)
        cls.mocker.result([{ 'lv_name' : 'mysql', 'vg_name' : 'dba' }])
        # mock blkid too
        blkid = cls.mocker.replace('holland.lib.lvm.raw.blkid')
        blkid('/dev/dba/mysql')
        cls.mocker.result([{ 'type' : 'ext3' }])
        blkid(MATCH(lambda arg: arg != '/dev/dba/mysql'))
        cls.mocker.result([])
        cls.mocker.replay()
    setup_class = classmethod(setup_class)

    def teardown_class(cls):
        cls.mocker.restore()
    teardown_class = classmethod(teardown_class)

    def test_create(self):
        """Test creating a LogicalVolume"""
        lv = LogicalVolume({ 'lv_name' : 'mysql', 'vg_name' : 'dba' })
        assert_equals(lv.lv_name, 'mysql')

    def test_happy_lookup(self):
        """Test a loading an existing lv"""
        lv = LogicalVolume.lookup('dba/mysql')

    def test_filesystem(self):
        """Test looking up filesystem of lv"""
        lv = LogicalVolume.lookup('dba/mysql')
        assert_equals(lv.filesystem(), 'ext3')

    def test_bad_filesystem(self):
        """Test looking for filesystem of a lv that doesn't exist"""
        lv = LogicalVolume()
        lv.vg_name = 'dba'
        lv.lv_name = 'mysql_snapshot' # <- doesn't exist in our mock
        assert_raises(ValueError, lv.filesystem)

    def test_repr(self):
        lv = LogicalVolume.lookup('dba/mysql')
        assert_equals(repr(lv), 'LogicalVolume(device=\'/dev/dba/mysql\')')
