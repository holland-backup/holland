"""High-level Object Oriented LVM API"""

import os
from holland.lib.lvm.raw import pvs, vgs, lvs, blkid

class Volume(object):
    """Abstract Volume object for LVM Volume implementations

    This class should not directly be instantiated, but rather one
    of its subclasses such as PhysicalVolume, VolumeGroup or LogicalVolume
    """

    def __new__(cls, *args, **kwargs):
        if cls is Volume:
            raise NotImplementedError('Volume is an abstract base class and '
                                      'should not be directly instantiated')
        return super(Volume, cls).__new__(cls, *args, **kwargs)

    def __init__(self, attributes=()):
        self.attributes = dict(attributes)


    def __getattr__(self, key):
        try:
            return self.attributes[key]
        except KeyError:
            return super(Volume, self).__getattr__(key)
 
    def reload(self):
        """Reload a Volume with underlying data, which may have changed"""

        raise NotImplementedError()

    def lookup(cls, pathspec):
        """Lookup a volume for the pathspec given

        This will always return the first volume and raise an error
        if multiple volumes are found.

        :returns: Volume instance
        """
        raise NotImplementedError()
    lookup = classmethod(lookup)

    def search(cls, pathspec=None):
        """Search for volumes for the pathspec given

        This will search for any volumes matching the pathspec and return
        an iterable to walk across the volumes found.

        :returns: iterable of Volume instances
        """
        raise NotImplementedError()
    search = classmethod(search)

    def __repr__(self):
        return '%s(id=%s)' % (self.__class__.__name__, self.id)

class PhysicalVolume(Volume):
    """LVM Physical Volume representation"""

    def reload(self):
        """Reload this PhysicalVolume"""
        self.attributes, = pvs(self.pv_name)

    def lookup(cls, pathspec):
        """Lookup a physical volume for the pathspec given

        This will always return the first volume found and raise an error
        if multiple volumes match ``pathspec``

        :returns: PhysicalVolume instance
        """
        try:
            volume, = pvs(pathspec)
            return cls(volume)
        except ValueError:
            #XX: Perhaps we should be more specific :)
            raise
    lookup = classmethod(lookup)

    def search(cls, pathspec=None):
        """Search for volumes matching ``pathspec``

        This will search for any physical volumes matching ``pathspec`` and
        return an iterable that provides instance of PhysicalVolume

        :returns: iterable of PhysicalVolume instances
        """

        for volume in pvs(pathspec):
            yield volume
    search = classmethod(search)

    def __repr__(self):
        return "%s(device=%r)" % (self.__class__.__name__, self.pv_name)

class VolumeGroup(Volume):
    """LVM VolumeGroup representation"""

    def reload(self):
        """Reload this VolumeGroup"""
        self.attributes, = vgs(self.vg_name)

    def lookup(cls, pathspec):
        """Lookup a volume group for ``pathspec``

        This will always return the first volume group found and raise an error
        if multiple volumes match ``pathspec``

        :returns: VolumeGroup instance
        """
        try:
            volume, = vgs(pathspec)
            return cls(volume)
        except ValueError:
            #XX: Perhaps we should be more specific :)
            raise
    lookup = classmethod(lookup)

    def search(cls, pathspec=None):
        """Search for volume groups matching ``pathspec``

        This will search for any volume groups matching ``pathspec`` and
        return an iterable that provides instance of VolumeGroup

        :returns: iterable of VolumeGroup instances
        """

        for volume in vgs(pathspec):
            yield cls(volume)
    search = classmethod(search)

    def __repr__(self):
        return '%s(vg_name=%s)' % (self.__class__.__name__, self.vg_name)

class LogicalVolume(Volume):
    """LVM Logical Volume representation"""

    def lookup(cls, pathspec):
        """Lookup a logical volume for ``pathspec``

        This will always return the first volume group found and raise an error
        if multiple volumes match ``pathspec``

        :returns: LogicalVolume instance
        """
        try:
            volume, = lvs(pathspec)
            return cls(volume)
        except ValueError:
            #XX: Perhaps we should be more specific :)
            raise
    lookup = classmethod(lookup)

    def search(cls, pathspec=None):
        """Search for logical volumes matching ``pathspec``

        This will search for any logical volumes matching ``pathspec`` and
        return an iterable that provides instances of LogicalVolume

        :returns: iterable of LogicalVolume instances
        """

        for volume in lvs(pathspec):
            yield cls(volume)
    search = classmethod(search)

    def reload(self):
        """Reload the data for this LogicalVolume"""
        self.attributes, = lvs(self.device_name())

    def volume_group(self):
        """Lookup this LogicalVolume's volume_group
        
        :returns: VolumeGroup
        """
        return VolumeGroup.lookup(self.vg_name)

    def device_name(self):
        """Lookup the canonical device name for the underlying locail volume

        :returns: device name string
        """
        return os.path.realpath('/dev/' + self.vg_name + '/' + self.lv_name)

    def filesystem(self):
        """Lookup the filesystem type for the underyling logical volume

        :returns: filesystem type name string
        """
        try:
            device_info, = blkid(self.device_name())
            return device_info['type']
        except ValueError:
            raise
    filesystem = property(filesystem)

    def __repr__(self):
        return '%s(device=%r)' % (self.__class__.__name__, self.device_name())
