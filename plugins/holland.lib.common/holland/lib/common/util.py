"""
Helpful functions
"""

import os
import shutil
from string import Template

from holland.core.backup import BackupError


def parse_arguments(arguments, **kwargs):
    """Replace varibles with values"""
    if not arguments:
        return arguments
    if isinstance(arguments, list):
        arguments = " ".join(arguments)
    ret = Template(arguments).safe_substitute(**kwargs)
    ret = ret.split(" ")
    return ret


def get_cmd_path(cmd, mode=os.F_OK | os.X_OK, path=None, raise_when_not_found=True):
    """Find the full path to an executable command.

    Args:
        cmd (str): The command to find. If an absolute path is provided, it will be
            checked directly. Otherwise, the command name will be searched for
            in the provided PATH or environment PATH.
        mode (int, optional): The access mode to check. Defaults to os.F_OK | os.X_OK.
        path (str or list, optional): PATH string or list of directories to search.
            If not provided, uses the environment PATH.
        raise_when_not_found (bool, optional): If True, raises BackupError when command
            is not found. If False, returns None instead.

    Returns:
        str or None: The full path to the command if found. Returns None if the command
            is not found and raise_when_not_found is False.

    Raises:
        BackupError: If the command is not found and raise_when_not_found is True.
    """
    # If path is a list, convert it to a PATH string
    if path and isinstance(path, list):
        path = os.pathsep.join(path)
    # Fall back to environment PATH if no path is provided
    path = path or os.environ.get("PATH", "")
    try:
        cmd_path = shutil.which(cmd, mode=mode, path=path)
    except AttributeError:
        # shutil.which was added in python 3.3
        # Check if we were given an absolute path
        if os.path.isabs(cmd):
            cmd_path = cmd if os.access(cmd, mode) else None
        else:
            for path_dir in [p for p in path.split(os.pathsep) if p]:
                test_path = os.path.join(path_dir, cmd)
                if os.access(test_path, mode):
                    cmd_path = test_path
                    break
    if not cmd_path and raise_when_not_found:
        raise BackupError("Failed to find '%s' in PATH: %s" % (cmd, path))
    return cmd_path
