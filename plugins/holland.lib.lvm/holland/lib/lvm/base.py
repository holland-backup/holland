"""High-level Object Oriented LVM API"""

import os
import logging
from holland.lib.lvm.raw import pvs, vgs, lvs, lvsnapshot, lvremove, mount, umount, blkid
from holland.lib.lvm.util import getdevice
from holland.lib.lvm.errors import LVMCommandError

LOG = logging.getLogger(__name__)


class Volume(object):
    """Abstract Volume object for LVM Volume implementations

    This class should not directly be instantiated, but rather one
    of its subclasses such as PhysicalVolume, VolumeGroup or LogicalVolume
    """

    # pylint: disable=unused-argument
    def __new__(cls, attributes=()):
        if cls is Volume:
            raise NotImplementedError(
                "Volume is an abstract base class and " "should not be directly instantiated"
            )
        return super(Volume, cls).__new__(cls)

    def __init__(self, attributes=()):
        self.attributes = dict(attributes)

    def __getattr__(self, key):
        try:
            return self.attributes[key]
        except KeyError:
            return super(Volume, self).__getattribute__(key)

    def reload(self):
        """Reload a Volume with underlying data, which may have changed"""

        raise NotImplementedError()

    @classmethod
    def lookup(cls, pathspec):
        """Lookup a volume for the pathspec given

        This will always return the first volume and raise an error
        if multiple volumes are found.

        :returns: Volume instance
        """
        raise NotImplementedError()

    @classmethod
    def search(cls, pathspec=None):
        """Search for volumes for the pathspec given

        This will search for any volumes matching the pathspec and return
        an iterable to walk across the volumes found.

        :returns: iterable of Volume instances
        """
        raise NotImplementedError()

    def __repr__(self):
        return "%s()" % (self.__class__.__name__,)


class PhysicalVolume(Volume):
    """LVM Physical Volume representation"""

    def reload(self):
        """Reload this PhysicalVolume"""
        self.attributes, = pvs(self.pv_name)

    @classmethod
    def lookup(cls, pathspec):
        """Lookup a physical volume for the pathspec given

        This will always return the first volume found and raise an error
        if multiple volumes match ``pathspec``

        :returns: PhysicalVolume instance
        """
        try:
            volume, = pvs(pathspec)
            return cls(volume)
        except (ValueError, LVMCommandError):
            raise LookupError("No PhysicalVolume could be found for " "pathspec %r" % pathspec)

    @classmethod
    def search(cls, pathspec=None):
        """Search for volumes matching ``pathspec``

        This will search for any physical volumes matching ``pathspec`` and
        return an iterable that provides instance of PhysicalVolume

        :returns: iterable of PhysicalVolume instances
        """

        for volume in pvs(pathspec):
            yield cls(volume)

    def __repr__(self):
        return "%s(device=%r)" % (self.__class__.__name__, self.pv_name)


class VolumeGroup(Volume):
    """LVM VolumeGroup representation"""

    def reload(self):
        """Reload this VolumeGroup"""
        self.attributes, = vgs(self.vg_name)

    @classmethod
    def lookup(cls, pathspec):
        """Lookup a volume group for ``pathspec``

        This will always return the first volume group found and raise an error
        if multiple volumes match ``pathspec``

        :returns: VolumeGroup instance
        """
        try:
            volume, = vgs(pathspec)
            return cls(volume)
        except (LVMCommandError, ValueError):
            raise LookupError("No VolumeGroup could be found for pathspec %r" % pathspec)

    @classmethod
    def search(cls, pathspec=None):
        """Search for volume groups matching ``pathspec``

        This will search for any volume groups matching ``pathspec`` and
        return an iterable that provides instance of VolumeGroup

        :returns: iterable of VolumeGroup instances
        """

        for volume in vgs(pathspec):
            yield cls(volume)

    def __repr__(self):
        return "%s(vg_name=%s)" % (self.__class__.__name__, self.vg_name)


class LogicalVolume(Volume):
    """LVM Logical Volume representation"""

    @classmethod
    def lookup(cls, pathspec):
        """Lookup a logical volume for ``pathspec``

        This will always return the first volume group found and raise an error
        if multiple volumes match ``pathspec``

        :returns: LogicalVolume instance
        """
        try:
            volume, = lvs(pathspec)
            return cls(volume)
        except (LVMCommandError, ValueError) as ex:
            # XX: Perhaps we should be more specific :)
            raise LookupError(
                "No LogicalVolume could be found " "for pathspec %r, %s" % (pathspec, ex)
            )
        except Exception as ex:
            raise OSError("unable to look up path %s" % ex)

    @classmethod
    def lookup_from_fspath(cls, path):
        """Lookup a logical volume for the filesystem path ``path``

        :returns: LogicalVolumeInstance
        """
        device = getdevice(path)
        return cls.lookup(device)

    @classmethod
    def search(cls, pathspec=None):
        """Search for logical volumes matching ``pathspec``

        This will search for any logical volumes matching ``pathspec`` and
        return an iterable that provides instances of LogicalVolume

        :returns: iterable of LogicalVolume instances
        """

        for volume in lvs(pathspec):
            yield cls(volume)

    def reload(self):
        """Reload the data for this LogicalVolume"""
        self.attributes, = lvs(self.device_name())

    def snapshot(self, name, size):
        """Snapshot the current LogicalVolume instance and create a snapshot
        volume with the requested volume name and size

        :param name: name of the volume
        :param size: size of the snapshot
        :raises: LVMCommandError on error
        :returns: LogicalVolume that is a snapshot of this one on success
        """

        try:
            lvsnapshot(self.device_name(), name, size)
        except LVMCommandError as exc:
            for line in exc.error.splitlines():
                LOG.error("%s", line)
            raise
        return LogicalVolume.lookup(self.vg_name + "/" + name)

    def is_mounted(self):
        """Check if this logical volume is mounted

        :returns: True if mounted and false otherwise
        """
        real_device_path = os.path.realpath(self.device_name())
        for line in open("/proc/mounts", "r"):
            dev = line.split()[0]
            if os.path.realpath(dev) == real_device_path:
                return True
        return False

    def mount(self, path, options=None):
        """Mount this volume on the specified path

        :param path: path where this volume should be mounted
        :param options: options to pass to mount
        """
        try:
            mount(self.device_name(), path, options)
        except LVMCommandError as exc:
            for line in exc.error.splitlines():
                LOG.error("%s", line)
            raise

    def unmount(self):
        """Unmount this volume, if mounted"""
        try:
            umount(self.device_name())
        except LVMCommandError as exc:
            for line in exc.error.splitlines():
                LOG.error("%s", line)
            raise

    def remove(self):
        """Remove this LogicalVolume

        The data on this object is not longer valid once this method
        successfully returns

        :raises: LVMCommandError on error
        """
        try:
            lvremove(self.device_name())
        except LVMCommandError as exc:
            for line in exc.error.splitlines():
                LOG.error("%s", line)
            raise

    def exists(self):
        """Check whether the volume currently exists

        :returns: bool. True if the volume exists or false otherwise
        """
        try:
            return self.lookup(self.device_name()) is not None
        except (LookupError, LVMCommandError):
            return False

    def volume_group(self):
        """Lookup this LogicalVolume's volume_group

        :returns: VolumeGroup
        """
        return VolumeGroup.lookup(self.vg_name)

    def device_name(self):
        """Lookup the canonical device name for the underlying locail volume

        :returns: device name string
        """
        return "/dev/" + self.vg_name + "/" + self.lv_name

    def filesystem(self):
        """Lookup the filesystem type for the underyling logical volume

        :returns: filesystem type name string
        """
        try:
            device_info, = blkid(self.device_name())
            LOG.debug("Looked up device_info => %r", device_info)
            return device_info["type"]
        except (LVMCommandError, ValueError) as exc:
            LOG.debug(
                "Failed looking up filesystem for %s => %r", self.device_name(), exc, exc_info=True
            )
            raise

    def __repr__(self):
        return "%s(device=%r)" % (self.__class__.__name__, self.device_name())
