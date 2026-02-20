"""
Common which utils
"""

import os
import shutil

from holland.core.backup import BackupError


def which(cmd):
    """Returns full path to command or else raises an error"""
    try:
        full_path = shutil.which(cmd)
        if full_path:
            return full_path
    except AttributeError:
        # shutil.which was added in python 3.3
        for path in os.environ["PATH"].split(":"):
            try:
                for path_cmd in os.listdir(path):
                    if cmd == path_cmd:
                        return os.path.join(path, cmd)
            except OSError:
                pass
    raise BackupError("No command found '%s'" % cmd)
