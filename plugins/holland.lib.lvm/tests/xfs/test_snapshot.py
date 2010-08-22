import shutil
from nose.tools import *
from holland.lib.lvm import LogicalVolume
from holland.lib.lvm.snapshot import *
from tests.constants import *

class TestSnapshot(object):
    def setup(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.tmpdir)
 
    def test_snapshot_fsm(self):
        lv = LogicalVolume.lookup('%s/%s' % (TEST_VG, TEST_LV))
        name = lv.lv_name + '_snapshot'
        size = 1 # extent

        snapshot = Snapshot(name, size, self.tmpdir)
        snapshot.start(lv)

    def test_snapshot_fsm_with_callbacks(self):
        lv = LogicalVolume.lookup('%s/%s' % (TEST_VG, TEST_LV))
        name = lv.lv_name + '_snapshot'
        size = 1 # extent

        snapshot = Snapshot(name, size, self.tmpdir)
        def handle_event(event, *args, **kwargs):
            pass

        snapshot.register('pre-mount', handle_event)
        snapshot.register('post-mount', handle_event)
        snapshot.start(lv)

    def test_snapshot_fsm_with_failures(self):
        lv = LogicalVolume.lookup('%s/%s' % (TEST_VG, TEST_LV))
        name = lv.lv_name + '_snapshot'
        size = 1 # extent

        snapshot = Snapshot(name, size, self.tmpdir)

        def bad_callback(event, *args, **kwargs):
            raise Exception("Oooh nooo!")

        for evt in ('initialize', 'pre-snapshot', 'post-snapshot', 
                    'pre-mount', 'post-mount', 'pre-unmount', 'post-unmount',
                    'pre-remove', 'post-remove', 'finish'):
            snapshot.register(evt, bad_callback)
            assert_raises(CallbackFailuresError, snapshot.start, lv)
            snapshot.unregister(evt, bad_callback)
            if snapshot.sigmgr._handlers:
                raise Exception("WTF. sigmgr handlers still exist when checking event => %r", evt)
