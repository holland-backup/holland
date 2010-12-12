"""LVM Snapshot state machine"""

import sys
import signal
import logging
from holland.lib.lvm.errors import LVMCommandError
from holland.lib.lvm.util import SignalManager, format_bytes

LOG = logging.getLogger(__name__)

__all__ = [
    'Snapshot',
    'CallbackFailuresError',
]

class Snapshot(object):
    """Snapshot state machine"""
    def __init__(self, name, size, mountpoint):
        self.name = name
        self.size = size
        self.mountpoint = mountpoint
        self.callbacks = {}
        self.sigmgr = SignalManager()

    def start(self, volume):
        """Start the snapshot process to snapshot the logical volume
        that ``path`` exists on.

        """
        self.sigmgr.trap(signal.SIGINT)
        try:
            self._apply_callbacks('initialize', self)
        except CallbackFailuresError, exc:
            return self.error(None, exc)
        return self.create_snapshot(volume)

    def create_snapshot(self, logical_volume):
        """Create a snapshot for the given logical volume

        """

        try:
            self._apply_callbacks('pre-snapshot', self, None)
            snapshot = logical_volume.snapshot(self.name, self.size)
            LOG.info("Created snapshot volume %s", snapshot.device_name())
        except (LVMCommandError, CallbackFailuresError), exc:
            return self.error(None, exc)

        try:
            self._apply_callbacks('post-snapshot', self, snapshot)
        except CallbackFailuresError, exc:
            return self.error(snapshot, exc)

        return self.mount_snapshot(snapshot)

    def mount_snapshot(self, snapshot):
        """Mount the snapshot"""

        try:
            self._apply_callbacks('pre-mount', self, snapshot)
            options = None
            if snapshot.filesystem() == 'xfs':
                LOG.info("xfs filesystem detected on %s. "
                         "Using mount -o nouuid",
                         snapshot.device_name())
                options = 'nouuid'
            snapshot.mount(self.mountpoint, options)
            LOG.info("Mounted %s on %s",
                     snapshot.device_name(), self.mountpoint)
            self._apply_callbacks('post-mount', self, snapshot)
        except LVMCommandError, exc:
            LOG.error("%s", exc)
            for line in exc.error.splitlines():
                LOG.error("%s", line)
            return self.error(snapshot, exc)
        except CallbackFailuresError, exc:
            return self.error(snapshot, exc)

        return self.unmount_snapshot(snapshot)

    def unmount_snapshot(self, snapshot):
        """Unmount the snapshot"""
        try:
            self._apply_callbacks('pre-unmount', snapshot)
            snapshot.unmount()
            LOG.info("Unmounted %s", snapshot.device_name())
        except (CallbackFailuresError, LVMCommandError), exc:
            return self.error(snapshot, exc)

        try:
            self._apply_callbacks('post-unmount', snapshot)
        except CallbackFailuresError, exc:
            return self.error(snapshot, exc)

        return self.remove_snapshot(snapshot)

    def remove_snapshot(self, snapshot):
        """Remove the snapshot"""
        try:
            self._apply_callbacks('pre-remove', snapshot)
            snapshot.remove()
            LOG.info("Removed snapshot %s", snapshot.device_name())
        except (CallbackFailuresError, LVMCommandError), exc:
            return self.error(snapshot, exc)

        try:
            self._apply_callbacks('post-remove', snapshot)
        except (CallbackFailuresError), exc:
            return self.error(snapshot, exc)

        return self.finish()

    def finish(self):
        """Finish the snapshotting process"""
        self.sigmgr.restore()
        self._apply_callbacks('finish', self)
        if sys.exc_info()[1]:
            raise

    def error(self, snapshot, exc):
        """Handle an error during the snapshot process"""
        LOG.debug("Error encountered during snapshot processing: %s", exc)

        if snapshot and snapshot.exists():
            snapshot.reload()
            if 'S' in snapshot.lv_attr:
                LOG.error("Snapshot space (%s) exceeded. "
                          "Snapshot %s is no longer valid",
                          snapshot.device_name(),
                          format_bytes(int(snapshot.lv_size)))
            try:
                if snapshot.is_mounted():
                    snapshot.unmount()
                    LOG.info("Unmounting snapshot %s on cleanup",
                             snapshot.device_name())
                if snapshot.exists():
                    snapshot.remove()
                    LOG.info("Removed snapshot %s on cleanup",
                             snapshot.device_name())
            except LVMCommandError, exc:
                LOG.error("Failed to remove snapshot %s", exc)

        return self.finish()

    def register(self, event, callback, priority=100):
        """Register a callback for ``event`` with ``priority``

        """
        self.callbacks.setdefault(event, []).append((priority, callback))

    def unregister(self, event, callback):
        """Remove a previously registered callback"""
        pending = []
        for info in self.callbacks.get(event, []):
            if callback in info:
                pending.append(info)

        for item in pending:
            self.callbacks[event].remove(item)

    def _apply_callbacks(self, event, *args, **kwargs):
        """Apply callbacks for event"""
        callback_list = list(self.callbacks.get(event, []))
        callback_list.sort()
        callback_list.reverse()
        callback_list = [callback[1] for callback in callback_list]
        for callback in callback_list:
            try:
                LOG.debug("Calling %s", callback)
                callback(event, *args, **kwargs)
            except:
                LOG.debug("Callback %r failed for event %s",
                          callback, event, exc_info=True)
                exc = sys.exc_info()[1]
                raise CallbackFailuresError([(callback, exc)])


class CallbackFailuresError(Exception):
    """Error running callbacks"""

    def __init__(self, errors):
        Exception.__init__(self, errors)
        self.errors = errors

