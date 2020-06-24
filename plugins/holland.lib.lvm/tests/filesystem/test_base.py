""" Test ext lvm """
import logging
import unittest
from tempfile import mkdtemp

from holland.lib.lvm.base import VolumeGroup, PhysicalVolume, LogicalVolume, Volume
from holland.lib.lvm.errors import LVMCommandError
from holland.lib.lvm.util import getdevice
from tests.constants import TEST_VG, TEST_LV

from . import setup, teardown


class TestPhysicalVolume(unittest.TestCase):
    """ Test pv commands"""

    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()
        setup(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.tmpdir)

    def test_create(self):
        """Test creating a physical volume"""

    def test_reload(self):
        """Test reloading a PhysicalVolume"""
        phy_vol = PhysicalVolume.lookup("/dev/loop0")
        self.assertEqual(phy_vol.pv_name, "/dev/loop0")
        phy_vol.reload()
        self.assertEqual(phy_vol.pv_name, "/dev/loop0")

    def test_lookup(self):
        """Test looking up a single physical volume"""
        phy_vol = PhysicalVolume.lookup("/dev/loop0")
        self.assertEqual(phy_vol.pv_name, "/dev/loop0")

    def test_lookup_failure(self):
        """Test looking up an invalid pv"""
        self.assertRaises(LookupError, PhysicalVolume.lookup, "/dev/loop1")

    def test_search(self):
        """Test searching for a physical volume"""
        # stupid simple test to make sure we're returning an iterable
        result = PhysicalVolume.search("/dev/loop0")
        self.assertTrue(not isinstance(result, Volume))
        phy_vol = next(result)
        self.assertTrue(isinstance(phy_vol, PhysicalVolume), "not a physical volume? %r" % phy_vol)
        self.assertRaises(StopIteration, result.__next__)

    def test_repr(self):
        """ Test Name """
        phy_vol = PhysicalVolume.lookup("/dev/loop0")
        self.assertEqual(repr(phy_vol), "PhysicalVolume(device='/dev/loop0')")


class TestVolumeGroup(unittest.TestCase):
    """ Test vg commands"""

    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()
        setup(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.tmpdir)

    def test_create(self):
        """Create VG"""
        vol_group = VolumeGroup({"vg_name": "dba", "vg_extent_size": 4 * 1024 ** 2})
        self.assertEqual(vol_group.vg_name, "dba")
        self.assertEqual(vol_group.vg_extent_size, 4194304)

    def test_lookup(self):
        """Lookup VG"""
        vol_group = VolumeGroup.lookup("holland")
        self.assertEqual(vol_group.vg_name, "holland")
        self.assertEqual(vol_group.lv_count, "1")  # only holland/test_lv is created
        self.assertEqual(vol_group.pv_count, "1")  # only /dev/loopN is assigned

    def test_failing_lookup(self):
        """Lookup fake VG"""
        self.assertRaises(LookupError, VolumeGroup.lookup, "holland_missing")

    def test_search(self):
        """Test VG search"""
        for vol_group in VolumeGroup.search("holland"):
            self.assertEqual(vol_group.vg_name, "holland")
            self.assertEqual(vol_group.lv_count, "1")  # only holland/test_lv is created
            self.assertEqual(vol_group.pv_count, "1")  # only /dev/loopN is assigned

    def test_reload(self):
        """Reload VG"""
        vol_group = VolumeGroup.lookup("holland")
        vol_group.reload()
        self.assertEqual(vol_group.vg_name, "holland")

    def test_repr(self):
        """Test Naming"""
        vol_group = VolumeGroup.lookup("holland")
        self.assertEqual(repr(vol_group), "VolumeGroup(vg_name=holland)")


class TestLogicalVolume(unittest.TestCase):
    """ Test lv commands"""

    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()
        setup(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.tmpdir)

    def test_create(self):
        """Test creating a LogicalVolume"""
        log_vol = LogicalVolume({"lv_name": "mysql", "vg_name": "dba"})
        self.assertEqual(log_vol.lv_name, "mysql")

    def test_happy_lookup(self):
        """Test a loading an existing lv"""
        log_vol = LogicalVolume.lookup("holland/test_lv")
        self.assertEqual(log_vol.vg_name, "holland")
        self.assertEqual(log_vol.lv_name, "test_lv")

    def test_sad_lookup(self):
        """Test fake lookup"""
        self.assertRaises(LookupError, LogicalVolume.lookup, "holland/test_lv_missing")

    def test_look_path(self):
        """Lookup path"""
        log_vol = LogicalVolume.lookup_from_fspath(self.__class__.tmpdir)
        self.assertEqual(log_vol.vg_name, TEST_VG)
        self.assertEqual(log_vol.lv_name, TEST_LV)

    def test_search(self):
        """Search for LG"""
        for log_vol in LogicalVolume.search("%s/%s" % (TEST_VG, TEST_LV)):
            self.assertEqual(log_vol.vg_name, TEST_VG)
            self.assertEqual(log_vol.lv_name, TEST_LV)

    def test_reload(self):
        """Reload LG"""
        log_vol = LogicalVolume.lookup(TEST_VG)
        log_vol.reload()
        self.assertEqual(log_vol.lv_name, TEST_LV)

    def test_snapshot(self):
        """Test snapshot"""
        log_vol = LogicalVolume.lookup("%s/%s" % (TEST_VG, TEST_LV))
        snapshot = None
        try:
            snapshot = log_vol.snapshot(log_vol.lv_name + "_snapshot", 1)
            self.assertTrue(log_vol != snapshot)
            self.assertTrue("s" in snapshot.lv_attr)
            self.assertEqual(snapshot.lv_size, snapshot.vg_extent_size)
            snapshot.mount(self.__class__.tmpdir)
            self.assertTrue(snapshot.is_mounted())
            self.assertEqual(
                getdevice(self.__class__.tmpdir), "/dev/mapper/holland-test_lv_snapshot"
            )
            log_vol.reload()
            snapshot.unmount()
            self.assertEqual(snapshot.is_mounted(), False)
            snapshot.remove()
            self.assertTrue(not snapshot.exists())
            snapshot = None
        finally:
            if snapshot and snapshot.is_mounted():
                snapshot.unmount()
            if snapshot and snapshot.exists():
                snapshot.remove()

    def test_filesystem(self):
        """Test looking up filesystem of lv"""
        log_vol = LogicalVolume.lookup("holland/test_lv")
        logging.warning("Loaded logical volume log_vol => %r", log_vol)
        self.assertTrue(log_vol.exists())
        self.assertEqual(log_vol.filesystem(), "ext3")

    def test_bad_filesystem(self):
        """Test looking for filesystem of a lv that doesn't exist"""
        log_vol = LogicalVolume()
        log_vol.vg_name = "holland"
        log_vol.lv_name = "test_lv_missing"  # <- doesn't exist in our setup
        self.assertRaises(LVMCommandError, log_vol.filesystem)

    def test_volume_group(self):
        """Test VG"""
        log_vol = LogicalVolume.lookup("%s/%s" % (TEST_VG, TEST_LV))
        vol_group = log_vol.volume_group()
        self.assertEqual(vol_group.vg_name, log_vol.vg_name)
        self.assertEqual(vol_group.vg_extent_size, log_vol.vg_extent_size)

    def test_repr(self):
        """Test name"""
        log_vol = LogicalVolume.lookup("holland/test_lv")
        self.assertEqual(repr(log_vol), "LogicalVolume(device='/dev/holland/test_lv')")
