"""LVM formatting and validation methods"""

import os
import re
import signal
from math import log

__all__ = [
    'getmount',
    'getdevice',
    'relpath',
    'format_bytes',
    'SignalManager',
]

def getmount(path):
    """Return the mount point of a path
    
    :param path: path to find the mountpoint for

    :returns: str mounpoint path
    """

    path = os.path.realpath(path)

    while path != os.path.sep:
        if os.path.ismount(path):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    return path

def getdevice(mountpoint):
    """Return the device name for the given mountpoint
    
    This method should return the "top" device for the last device
    mounted on path, in case there are multiple stacked mounts

    :param mountpoint: mountpoint path to find the underlying device for

    :returns: str device path
    """

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
        exponent = int(log(abs(bytes), 1024))
    else:       
        exponent = 0

    return "%.*f%s" % (
        precision,
        bytes / (1024 ** exponent),
        ['Bytes','KB','MB','GB','TB','PB','EB','ZB','YB'][int(exponent)]
    )


class SignalManager(object):
    """Manage signals around critical sections"""

    def __init__(self):
        self.pending = []
        self._handlers = {}

    def trap(self, *signals):
        """Request the set of signals to be trapped """
        for sig in signals:
            prev = signal.signal(sig, self._trap_signal)
            self._handlers[sig] = prev

    def _trap_signal(self, signum, *args):
        """Trap a signal and note it in this instance's pending list"""
        args = args
        self.pending.append(signum)

    def restore(self):
        """Clear pending signals and release trapped signals, restoring the
        original handlers
        """
        del self.pending[:]
        for sig in self._handlers:
            signal.signal(sig, self._handlers[sig])

