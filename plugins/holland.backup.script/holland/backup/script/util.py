"""Utility methods"""
import re
import logging
from string import Template
from subprocess import Popen, PIPE

LOG = logging.getLogger(__name__)

def size_to_bytes(size):
    """Parse a MySQL-like size string into bytes

    >> size_to_bytes('4G')
    4294967296
    """
    size = str(size)
    units = "bBkKmMgGtTpPeE"
    match = re.match(r'^(\d+(?:[.]\d+)?)([%s])?$' % units, size)
    if not match:
        raise ValueError("Invalid constant size syntax %r" % size)
    number, unit = match.groups()
    if not unit:
        unit = 'B'
    unit = unit.upper()
    exponent = "BKMGTPE".find(unit)
    return int(float(number)*1024**exponent)

def cmd_to_size(cmd):
    """Run a command and interpret its output through
    size_to_bytes

    >> cmd_to_size('echo 4G')
    4294967296
    """
    pid = Popen(cmd,
                shell=True,
                stdout=PIPE,
                stderr=PIPE,
                close_fds=True)
    stdout, stderr = pid.communicate()

    for line in str(stderr).splitlines():
        LOG.info("- %s", line.rstrip())
    return size_to_bytes(str(stdout).strip())
