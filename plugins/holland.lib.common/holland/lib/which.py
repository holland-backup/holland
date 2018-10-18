"""
Common which utils
"""

import sys
import os
import shutil
from holland.core.backup import BackupError

def which(cmd):
    try:
        full_path = shutil.which(cmd)
        if full_path:
            return full_path
    except AttributeError:
            #shutil.which was added in python 3.3
            for path in sys.path:
                try:
                    if any(path.startswith(cmd) for path in os.listdir(path)):
                        return os.path.join(path, cmd)
                except OSError:
                    pass
    raise BackupError("No command found for compression method '%s'" % cmd)
