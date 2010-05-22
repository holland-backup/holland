"""LVM Snapshot state machine"""

import logging
from holland.lib.lvm import LogicalVolume

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

    def start(self, path):
        """Start the snapshot process to snapshot the logical volume
        that ``path`` exists on.

        """
        try:
            logical_volume = LogicalVolume.lookup_from_path(path)
        except Exception:
            return self.error(None)
        return self.create_snapshot(logical_volume)

    def create_snapshot(self, logical_volume):
        """Create a snapshot for the given logical volume

        """
        try:
            snapshot = logical_volume.snapshot(self.name, self.size)
        except Exception:
            return self.error(None)

        return self.mount_snapshot(snapshot)

    def mount_snapshot(self, snapshot):
        """Mount the snapshot"""
        try:
            snapshot.mount(self.mountpoint)
        except Exception:
            return self.error(snapshot)

        return self.unmount_snapshot(snapshot)

    def unmount_snapshot(self, snapshot):
        """Unmount the snapshot"""
        try:
            snapshot.unmount()
        except Exception:
            return self.error(snapshot)

        return self.remove_snapshot(snapshot)

    def remove_snapshot(self, snapshot):
        """Remove the snapshot"""
        try:
            snapshot.remove()
        except Exception:
            return self.error(snapshot)

        return self.finish()

    def finish(self):
        """Finish the snapshotting process"""
        pass

    def error(self, snapshot):
        if snapshot:
            try:
                snapshot.unmount()
            except:
                pass
            try:
                snapshot.remove()
            except:
                pass

    def register(self, event, callback, priority=100):
        """Register a callback for ``event`` with ``priority``

        """
        self.callbacks.setdefault(event, []).append((priority, callback))

    def _apply_callbacks(self, event, *args, **kwargs):
        """Apply callbacks for event"""
        callback_list = list(self.callbacks.get(event, []))
        callback_list.sort(reverse=True)
        callback_list = [callback[1] for callback in callback_list]
        errors = []
        for callback in callback_list:
            try:
                callback(event, *args, **kwargs)
            except Exception, exc:
                errors.append((callback, exc))

        if errors:
            raise CallbackFailuresError(errors)

class CallbackFailuresError(Exception):
    """Error running callbacks"""
    pass
