"""LVM formatting and validation methods"""

import re
from math import log


import os
import math

__all__ = [
    'getmount',
    'getdevice',
    'relpath',
    'format_bytes',
    'format_size',
    'parse_size',
    'validate_size',
    'validate_name',
]

def format_size(bytes, precision=4):
    """
    Format an integer number of bytes to a human
    readable string.

    """
    units = "KMGTPE"

    if bytes < 1024:
        raise ValueError("LVM does not support units lower than 1K")

    exponent = int(log(abs(bytes), 1024))

    # Offset into our units sequence
    # min = 0, max = 5 (E => exabytes)
    unit_index = min(max(exponent - 1, 0), len(units) - 1)

    # limit exponent for very large units
    exponent = min(exponent, len(units))

    return "%.*f%s" % (
        precision,
        bytes / (1024.0 ** exponent),
        units[unit_index]
    )

def parse_size(units_string):
    """Parse an LVM size string into bytes"""

    units_string = str(units_string)

    units = "kKmMgGtTpPeE"

    match = re.match(r'^(\d+(?:[.]\d+)?)([%s]|)$' % units, units_string)
    if not match:
        raise ValueError("Invalid LVM Unit syntax %r" % units_string)
    number, unit = match.groups()
    if not unit:
        unit = 'M'
    unit = unit.upper()

    exponent = "KMGTPE".find(unit)

    return int(float(number) * 1024 ** (exponent + 1))

def validate_lvm_size(units_string):
    """Validate an LVM size specification"""
    return format_size(parse_size(units_string))

def validate_lvm_name(lv_or_vg_name):
    """Validate an LVM object name according the spec from lvm(8)"""
    # ., .. are prohibited for VG
    # additionally, LV also cannot be named snapshot or pvmove
    prohibited_names = ('.', '..', 'snapshot', 'pvmove')
    # These only apply to LVs and may not appear anywhere in the name
    prohibited_patterns = ('_mlog', '_mimage')
    namecre = re.compile(r'^[a-zA-Z0-9+_.][a-zA-Z0-9+_.-]*$')
    for name in prohibited_names:
        if name == lv_or_vg_name:
            raise ValueError("Invalid name %r" % lv_or_vg_name)
    for pat in prohibited_patterns:
        if pat in lv_or_vg_name:
            raise ValueError("LV may not contain %r" % pat)

    if namecre.match(lv_or_vg_name) is None:
        # This is really a lexical error, right?
        raise ValueError("Invalid name %r" % lv_or_vg_name)


def getmount(path):
    """Return the mount point of a path"""

    path = os.path.realpath(path)

    while path != os.path.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path

def getdevice(mountpoint):
    """Return the device name for the given mountpoint"""

    if not os.path.exists(mountpoint):
        # don't return a device for a non-existent mountpoint
        return None

    mountpoint = getmount(mountpoint)

    # Read /proc/mounts in reverse order to get the right mountpoint
    # for a stacked mount, as these should be appended to the end

    # For py23 support 'reversed' doesn't exist, so call list.reverse()
    # explicitly
    proc_mounts_info = open('/proc/mounts', 'r').readlines()
    proc_mounts_info.reverse()

    for path in proc_mounts_info:
        device, mount = path.split()[0:2]
        # handle path with spaces - encoded in /etc/mtab
        mount = mount.decode('string_escape')
        mount = os.path.normpath(mount)
        if mount == mountpoint:
            return device

# Taken from posixpath in Python2.6
def relpath(path, start=os.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.sep)
    path_list = os.path.abspath(path).split(os.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return os.curdir
    return os.path.join(*rel_list)

def format_bytes(bytes, precision=2):
    """Format an integer number of bytes to a human readable string."""

    if bytes != 0:
        exponent = int(math.log(abs(bytes), 1024))
    else:       
        exponent = 0

    return "%.*f%s" % (
        precision,
        bytes / (1024 ** exponent),
        ['Bytes','KB','MB','GB','TB','PB','EB','ZB','YB'][int(exponent)]
    )
