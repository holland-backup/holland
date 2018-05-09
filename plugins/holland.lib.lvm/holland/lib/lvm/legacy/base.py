"""Object Oriented LVM interface"""

import os
import logging
from holland.backup.lvm.util.path import getmount, getdevice
from api import is_lvm_device, pvs, vgs, lvs, mount, unmount, \
                lvsnapshot, lvremove, LVMError
from fmt import format_size, parse_size

__all__ = [
    'PhysicalVolume',
    'VolumeGroup',
    'LogicalVolume',
    'LVMError'
]

class PhysicalVolume(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def find_one(cls, name):
        for pvinfo in pvs(name):
            return PhysicalVolume(**pvinfo)
    find_one = classmethod(find_one)

class VolumeGroup(object):
    """LVM Volume Group"""
    def __init__(self, **kwargs):
        # silence pylint
        self.vg_name = None
        self.__dict__.update(kwargs)

    def find_all(cls, name):
        """Find all volume groups matching the given name"""
        result = []
        for vginfo in vgs(name):
            logging.debug("Creating VolumeGroup from info %r", vginfo)
            result.append(VolumeGroup(**vginfo))
        return result
    find_all = classmethod(find_all)
    find = find_all

    def find_one(cls, name):
        """Find first LVM volume group matching the given name"""
        for vginfo in vgs(name):
            logging.debug("Creating VolumeGroup from info %r", vginfo)
            return VolumeGroup(**vginfo)
    find_one = classmethod(find_one)

    def lvs(self):
        """List logical volumes for this volume group"""
        lv_list = LogicalVolume.find(None)
        result = []
        for logical_volume in lv_list:
            if logical_volume.vg_name == self.vg_name:
                result.append(logical_volume)
        return result
    lvs = property(lvs)

    def __str__(self):
        """String representation of this volume group"""
        return repr(self)

    def __repr__(self):
        """Representation of this volume group"""
        attributes = ['%s=%r' % (key, value)
                        for key, value in list(self.__dict__.items())
                            if key != 'self']
        return 'VolumeGroup(%s)' % ','.join(attributes)

class LogicalVolume(object):
    """LVM Logical Volume"""

    # 15G max snapshot size in bytes
    # Used when no snapshot size is provided
    MAX_SNAPSHOT_SIZE = 15*1024**3

    def __init__(self, **kwargs):
        # silence pylint
        self.vg_name = None
        self.lv_name = None
        self.lv_attr = None
        self.__dict__.update(kwargs)

    def find_all(cls, name):
        """Find all logical volumes matching name"""
        result = []
        for lvinfo in lvs(name):
            result.append(LogicalVolume(**lvinfo))
        return result
    find_all = classmethod(find_all)
    find = find_all

    def find_one(cls, name):
        """Find the first logical volume matching name"""
        for lvinfo in lvs(name):
            return LogicalVolume(**lvinfo)
    find_one = classmethod(find_one)

    def find_mounted(cls, path):
        """Find a currently mounted logical volume by mountpoint path"""
        dev = getdevice(getmount(path))
        try:
            return cls.find_one(dev)
        except LVMError as exc:
            logging.debug("Failed to find logical volume for device %r (path=%r): %s", dev, path, exc)
            return None
    find_mounted = classmethod(find_mounted)

    def vgs(self):
        """Find volume group for this Logical Volume"""
        vg_list = VolumeGroup.find(self.vg_name)

        logging.debug("vg_list => %r", vg_list)
        #assert len(vg_list) != 0,
        #    "No volume group found for logical volume %r" % \
        # (self.lv_name)
        #assert len(vg_list) == 1,
        #    "More than one volume group found for logical volume %r" % \
        #   (self.vg_name)

        return vg_list[0]
    vgs = property(vgs)
    volume_group = vgs

    def device_path(self):
        """Find the canonical path for this logical volume

        This returns a string path of the form
        /dev/volume-group/logical-volume
        """
        return os.path.join(os.sep, 'dev',
                            self.volume_group.vg_name,
                            self.lv_name)
    device_path = property(device_path)

    def exists(self):
        """Check whether this logical volume still exists"""
        return os.path.exists(self.device_path)

    def is_mounted(self):
        """Check if this logical volume is mounted"""
        device = os.path.join('/dev', self.vg_name, self.lv_name)
        real_device_path = os.path.realpath(device)
        for line in open('/proc/mounts', 'r'):
            dev = line.split()[0]
            if os.path.realpath(dev) == real_device_path:
                return True
        else:
            return False

    def snapshot(self, name=None, size=None):
        """Snapshot this logical volume with specified name and size"""
        if not name:
            name = self.lv_name + '_snapshot'
        volume_group = self.volume_group
        if not size:
            vg_size = int(volume_group.vg_size)
            vg_free = int(volume_group.vg_free)
            size = min(vg_size*0.2, vg_free, self.MAX_SNAPSHOT_SIZE)
        else:
            size = parse_size(size)

        # floor division to avoid exceeding the actual available extents
        snapshot_extents = size // int(volume_group.vg_extent_size)

        if snapshot_extents == 0:
            raise LVMError("No free snapshot space on %s" % str(self))

        if snapshot_extents > volume_group.vg_free_count:
            raise LVMError(
                "Excessive snapshot size (%s) exceeds free extents (%d)." % \
                    (size, self.vg_free_count)
                )

        lvsnapshot(lv_name='/'.join([self.vg_name, self.lv_name]),
                   snapshot_name=name,
                   snapshot_extents=snapshot_extents)

        return LogicalVolume.find('/'.join([self.vg_name, name]))[0]

    def mount(self, path):
        """Mount this logical volume and the specified path"""
        device = '/'.join(['/dev', self.vg_name, self.lv_name])
        logging.info("mounting %s to %s", device, path)
        options = None
        if fs_type(device) == 'xfs':
            options = 'nouuid'
        mount(device, path, options)
        assert self.is_mounted() is True, ("Mount of %s to %s failed " + \
                                           "even though mount() did " + \
                                           "not raise an error" % \
                                           (device, path))

    def unmount(self):
        """Unmount this logical volume"""
        device = '/'.join(['/dev', self.vg_name, self.lv_name])
        unmount(device)
        assert self.is_mounted() is False, "Unmount of %s failed" % (device,)

    def remove(self):
        """Remove this logical volume, if it is a snapshot"""
        try:
            self.refresh()
        except:
            logging.error("Failed to refresh %s", self)

        assert self.lv_attr[0] in 'sS', "Only snapshots can be " + \
                                        "removed via this API"

        if self.lv_attr[0] == 'S':
            logging.fatal("Snapshot %s exceeded size of %s",
                            os.path.join('/dev/', self.vg_name, self.lv_name),
                            format_size(int(self.lv_size)))

        if self.is_mounted():
            raise AssertionError("Logical volume %r is mounted." %
                os.path.join(self.vg_name, self.lv_name))
        lvremove('/'.join([self.vg_name, self.lv_name]))

    def refresh(self):
        """Refresh this LogicalVolume to match the underlying volume"""
        for lv in lvs():
            if lv['lv_uuid'] == self.lv_uuid:
                self.__dict__.update(lv)
                return
        else:
            raise LVMError("No system logical volume found with uuid %s" % self.lv_uuid)

    def __str__(self):
        extra = self.lv_attr in 'sS' and '[snapshot]' or ''
        return os.path.join("%s/dev" % extra,
                            self.vg_name, self.lv_name)

    def __repr__(self):
        attributes = ['%s=%r' % (key, value)
                        for key, value in list(self.__dict__.items())
                            if key != 'self']
        return "LogicalVolume(%s)" % ','.join(attributes)
