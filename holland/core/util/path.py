# $Id$
"""
Utility functions
"""

# Functions added here should really be as portable as possible
# and generally useful.

import os
import logging

LOG = logging.getLogger(__name__)


def ensure_dir(dir_path):
    """
    Ensure a directory path exists (by creating it if it doesn't).
    """

    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            LOG.debug("created directory %s", dir_path)
            return True
        except OSError as ex:
            # FIX ME: Need error codes/etc so this will exit(<code>) or raise
            # an appropriate holland exception
            LOG.error("os.makedirs(%s): %s", dir_path, ex)
            raise
    return False


def protected_path(path):
    """
    Take a path, and if the file/dir exist pass back a protected path
    (suffixed).

    Returns:

        string = new file path

    Example:

        >>> mypath = '/tmp'
        >>> new_path = helpers.protected_path(mypath)
        >>> new_path
        '/tmp.0'
    """
    safety = 0
    safe_path = path
    while True:
        if os.path.exists(safe_path):
            safe_path = "%s.%s" % (path, safety)
        else:
            break
        safety = safety + 1
    return safe_path


def format_bytes(input_bytes, precision=2):
    """
    Format an integer number of input_bytes to a human
    readable string.

    If input_bytes is negative, this method raises ArithmeticError
    """
    import math

    if input_bytes < 0:
        raise ArithmeticError("Only Positive Integers Allowed")

    if input_bytes != 0:
        exponent = math.floor(math.log(input_bytes, 1024))
    else:
        exponent = 0

    return "%.*f%s" % (
        precision,
        input_bytes / (1024 ** exponent),
        ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][int(exponent)],
    )


def normpath(path):
    """
    Normalize Path
    """
    return os.path.abspath(os.path.normpath(path))


def relpath(path, start=os.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = [x for x in os.path.abspath(start).split(os.sep) if x]
    path_list = [x for x in os.path.abspath(path).split(os.sep) if x]

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.pardir] * (len(start_list) - i) + path_list[i:]
    if not rel_list:
        return os.curdir
    return os.path.join(*rel_list)


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


def disk_capacity(target_path):
    """Find the total capacity of the filesystem that target_path is on

    :returns: integer number of input_bytes
    """
    path = getmount(target_path)
    info = os.statvfs(path)
    return info.f_frsize * info.f_blocks


def disk_free(target_path):
    """
    Find the amount of space free on a given path
    Path must exist.
    This method does not take into account quotas

    returns the size in input_bytes potentially available
    to a non privileged user
    """
    path = getmount(target_path)
    info = os.statvfs(path)
    return info.f_frsize * info.f_bavail


def directory_size(path):
    """
    Find the size of all files in a directory, recursively

    Returns the size in input_bytes on success
    """
    from os.path import join, getsize

    result = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            try:
                size = getsize(join(root, name))
                result = result + size
            except OSError:
                pass
        for name in dirs:
            LOG.debug("Debug: Determining size of directory %s", os.path.join(root, name))
    return result
