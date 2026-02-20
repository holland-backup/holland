# pylint: skip-file
""" Test Snapshot """
import unittest
from tempfile import mkdtemp

from holland.lib.lvm import LogicalVolume
from holland.lib.lvm.snapshot import Snapshot, CallbackFailuresError
from tests.constants import TEST_LV, TEST_VG

from . import setup, teardown


class TestSnapshot(unittest.TestCase):
    """Test Snapshot"""

    tmpdir = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()
        setup(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        teardown(cls.tmpdir)

    def test_snapshot_fsm(self):
        """Test snapshot"""
        log_vol = LogicalVolume.lookup("%s/%s" % (TEST_VG, TEST_LV))
        name = log_vol.lv_name + "_snapshot"
        size = 1  # extent

        snapshot = Snapshot(name, size, self.__class__.tmpdir)
        snapshot.start(log_vol)

    def test_snapshot_fsm_with_callbacks(self):
        """Test snapshot"""
        log_vol = LogicalVolume.lookup("%s/%s" % (TEST_VG, TEST_LV))
        name = log_vol.lv_name + "_snapshot"
        size = 1  # extent

        snapshot = Snapshot(name, size, self.__class__.tmpdir)

        def handle_event(event, *args, **kwargs):
            pass

        snapshot.register("pre-mount", handle_event)
        snapshot.register("post-mount", handle_event)
        snapshot.start(log_vol)

    def test_snapshot_fsm_with_failures(self):
        """Test Snapshot"""
        log_vol = LogicalVolume.lookup("%s/%s" % (TEST_VG, TEST_LV))
        name = log_vol.lv_name + "_snapshot"
        size = 1  # extent

        snapshot = Snapshot(name, size, self.__class__.tmpdir)

        def bad_callback(event, *args, **kwargs):
            raise Exception("Oooh nooo!")

        for evt in (
            "initialize",
            "pre-snapshot",
            "post-snapshot",
            "pre-mount",
            "post-mount",
            "pre-unmount",
            "post-unmount",
            "pre-remove",
            "post-remove",
            "finish",
        ):
            snapshot.register(evt, bad_callback)
            self.assertRaises(CallbackFailuresError, snapshot.start, log_vol)
            snapshot.unregister(evt, bad_callback)
            if snapshot.sigmgr._handlers:
                raise Exception(
                    "sigmgr handlers still exist when checking event => %r", evt
                )
