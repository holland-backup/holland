"""LVM API"""

from holland.lib.lvm.errors import LVMCommandError
from holland.lib.lvm.util import relpath, getmount, getdevice
from holland.lib.lvm.raw import pvs, vgs, lvs, blkid, mount, umount
from holland.lib.lvm.base import PhysicalVolume, VolumeGroup, LogicalVolume
from holland.lib.lvm.snapshot import Snapshot, CallbackFailuresError

__all__ = [
    'relpath',
    'getmount',
    'getdevice',
    'pvs',
    'vgs',
    'lvs',
    #'lvsnapshot',
    #'lvremove',
    'umount',
    'mount',
    #'LVMError',
    'PhysicalVolume',
    'VolumeGroup',
    'LogicalVolume',
    'Snapshot',
    'CallbackFailuresError',
]
