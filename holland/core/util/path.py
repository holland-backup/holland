"""Utility functions for manipulating paths """

# Functions added here should really be as portable as possible
# and generally useful.

import os

def relpath(origin, dest):
    """
    Find the relative path between origin and dest
    """
    parts = []
    origin = os.path.normpath(origin)
    dest = os.path.normpath(dest)

    if origin == dest:
        return ""

    path = dest
    while True:
        head, tail = os.path.split(path)

        if not tail:
            break

        if head == origin:
            return os.path.join('', *([tail] + parts))
        else:
            parts.insert(0, tail)
        path = head
    return None

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

def disk_free(target_path):
    """
    Find the amount of space free on a given path
    Path must exist.
    This method does not take into account quotas

    returns the size in bytes potentially available
    to a non privileged user
    """
    path = getmount(target_path)
    info = os.statvfs(path)
    return info.f_frsize*info.f_bavail

def directory_size(path):
    """
    Find the size of all files in a directory, recursively

    Returns the size in bytes on success
    """
    total_size = os.path.getsize(path)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            path = os.path.join(root, name)
            total_size += os.path.getsize(path)
        for name in files:
            path = os.path.join(root, name)
            try:
                nbytes = os.path.getsize(path)
                total_size += nbytes
            except OSError:
                pass
    return total_size
