"""Raw LVM command API"""

import re
import csv
from cStringIO import StringIO
from subprocess import Popen, PIPE, STDOUT

from holland.lib.lvm.constants import PVS_ATTR, VGS_ATTR, LVS_ATTR

class LVMError(Exception):
    """Error raised upon LVM problem"""

def pvs(*physical_volumes):
    """Report information about physical volumes

    :param volume_groups: volume groups to report on
    :returns: list of dicts of pvs parameters
    """
    pvs_args = [
        'pvs',
        '--unbuffered',
        '--noheadings',
        '--nosuffix',
        '--units=b',
        '--separator=,',
        '--options=%s' % ','.join(PVS_ATTR),
    ]
    pvs_args.extend(list(physical_volumes))
    process = Popen(pvs_args,
                    stdout=PIPE,
                    stderr=PIPE,
                    close_fds=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise LVMError('pvs', process.returncode, stderr)

    return parse_lvm_format(PVS_ATTR, stdout)

def vgs(*volume_groups):
    """Report information about volume groups

    :param volume_groups: volume groups to report on
    :returns: list of dicts of vgs parameters
    """
    vgs_args = [
        'vgs',
        '--unbuffered',
        '--noheadings',
        '--nosuffix',
        '--units=b',
        '--separator=,',
        '--options=%s' % ','.join(VGS_ATTR),
    ]
    vgs_args.extend(list(volume_groups))
    process = Popen(vgs_args,
                    stdout=PIPE,
                    stderr=PIPE,
                    close_fds=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise LVMError('vgs', process.returncode, stderr)

    return parse_lvm_format(VGS_ATTR, stdout)

def lvs(*volume_groups):
    """Report information about logical volumes

    `volume_groups` may refer to either an actual volume-group name or to a
    logical volume path to refer to a single logical volume

    :param volume_groups: volumes to report on
    :returns: list of dicts of lvs parameters
    """
    lvs_args = [
        'lvs',
        '--unbuffered',
        '--noheadings',
        '--nosuffix',
        '--units=b',
        '--separator=,',
        '--options=%s' % ','.join(LVS_ATTR),
    ]
    lvs_args.extend(list(volume_groups))
    process = Popen(lvs_args, 
                    stdout=PIPE, 
                    stderr=PIPE, 
                    close_fds=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise LVMError('lvs', process.returncode, stderr)

    return parse_lvm_format(LVS_ATTR, stdout)


def parse_lvm_format(keys, values):
    """Convert LVM tool output into a dictionary"""
    stream = StringIO(values)
    kwargs = dict(delimiter=',', skipinitialspace=True)
    for row in csv.reader(stream, **kwargs):
        yield dict(zip(keys, row))


## Filesystem utility functions
def blkid(*devices):
    """Locate/print block device attributes

    :param devices: devices to run blkid against
    :returns: iterable of dicts of blkid data
    """
    blkid_args = [
        'blkid',
    ]
    blkid_args.extend(list(devices))
    
    process = Popen(blkid_args,
                    stdout=PIPE,
                    stderr=PIPE,
                    close_fds=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise Exception('blkid', process.returncode, stderr)

    return parse_blkid_format(stdout)

def parse_blkid_format(text):
    """Parse the blkid output format

    :returns: iterable of dicts containing blkid information
    """
    blkid_cre = re.compile(r'(?P<device>.+?)[:] (?P<values>.*)')
    values_cre = re.compile(r'(?P<LABEL>[A-Z_]+)[=]"(?P<VALUE>[^"]+)')
    for line in text.splitlines():
        device, values = blkid_cre.match(line).group('device', 'values')
        key_values = [(key.lower(), value) for key, value 
                                            in values_cre.findall(values)]
        yield dict(key_values, device=device)

def mount(device, path, options=None, vfstype=None):
    """Mount a filesystem

    :raises: Exception
    """
    mount_args = [
        'mount',
    ]
    if options:
        mount_args.extend(['-o', options])
    if vfstype:
        mount_args.extend(['-t', vfstype])
    mount_args.extend([device, path])

    process = Popen(mount_args,
                    stdout=PIPE,
                    stderr=STDOUT,
                    close_fds=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise Exception('mount', process.returncode, stderr)

    return stdout

def umount(*path):
    """Unmount a file system

    :raises: Exception
    """
    process = Popen(['umount'] + list(path), 
                    stdout=PIPE, 
                    stderr=STDOUT, 
                    close_fds=True)

    stdout, stderr =  process.communicate()

    if process.returncode != 0:
        raise Exception('umount', process.returncode, stderr)

    return stdout

import os
os.environ['PATH'] = '/sbin:/usr/sbin:' + os.environ['PATH']
