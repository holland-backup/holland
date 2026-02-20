"""Test Raw filesystems"""
import os
import unittest
from tempfile import mkdtemp

from holland.lib.lvm.errors import LVMCommandError
from holland.lib.lvm.raw import blkid, lvremove, lvs, lvsnapshot, mount, umount, vgs
from tests.constants import IMG_SIZE, TEST_LV, TEST_VG

from . import setup, teardown


class TestRaw(unittest.TestCase):
    """Testing"""

    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()
        setup(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.tmpdir)

    def test_vgs(self):
        """Test VG"""
        (vol_group,) = vgs(TEST_VG)
        self.assertEqual(vol_group["vg_name"], TEST_VG)
        self.assertEqual(int(vol_group["pv_count"]), 1)

    def test_lvs(self):
        """Test lv"""
        (log_vol,) = lvs("%s/%s" % (TEST_VG, TEST_LV))
        self.assertEqual(log_vol["vg_name"], TEST_VG)

        vg_extents = int(log_vol["vg_extent_count"])
        self.assertEqual(int(vg_extents), 31)

        vg_extent_size = int(log_vol["vg_extent_size"])
        self.assertEqual(int(vg_extent_size), 4194304)

        self.assertEqual(int(log_vol["lv_size"]), IMG_SIZE / 2)

    def test_snapshot(self):
        """Test snapshot"""
        lvsnapshot("%s/%s" % (TEST_VG, TEST_LV), "%s_snapshot" % TEST_LV, 4, "512K")
        self.assertRaises(
            LVMCommandError,
            lvsnapshot,
            "%s/%s" % (TEST_VG, TEST_LV),
            "%s_snapshot" % TEST_LV,
            1,
        )
        mount(
            "/dev/%s/%s_snapshot" % (TEST_VG, TEST_LV),
            self.__class__.tmpdir,
            options="noatime",
            vfstype="ext3",
        )
        umount("/dev/%s/%s_snapshot" % (TEST_VG, TEST_LV))
        lvremove("%s/%s_snapshot" % (TEST_VG, TEST_LV))
        self.assertRaises(
            LVMCommandError, lvremove, "%s/%s_snapshot" % (TEST_VG, TEST_LV)
        )  # this should fail the 2nd time

    def test_blkid(self):
        """Test device info"""
        (info,) = blkid("/dev/%s/%s" % (TEST_VG, TEST_LV))
        self.assertEqual(info["type"], "ext3")

    def test_bad_mount(self):
        """Test mount failure"""
        self.assertRaises(
            LVMCommandError,
            mount,
            "/dev/%s/%s" % (TEST_VG, TEST_LV),
            os.path.join(self.__class__.tmpdir, "missing"),
        )
