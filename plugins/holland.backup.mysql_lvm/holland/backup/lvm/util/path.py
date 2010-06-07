import os
import math

__all__ = [
    'getmount',
    'getdevice',
    'relpath',
    'format_bytes'
]

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

    # For py23 support 'reversed' doesn't exist, so call
    # list.reverse() explicitly
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
