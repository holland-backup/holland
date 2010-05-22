"""Low level command interface to LVM"""

import os
import csv
import logging
from subprocess import Popen, PIPE, list2cmdline, call
from cStringIO import StringIO

LOG = logging.getLogger(__name__)

class CalledProcessError(Exception):
    """This exception is raised when a process run by check_call() returns
    a non-zero exit status.  The exit status will be stored in the
    returncode attribute."""
    def __init__(self, returncode, cmd):
        self.returncode = returncode
        self.cmd = cmd
        Exception.__init__()

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % \
                (self.cmd, self.returncode)   


def check_call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete.  If
    the exit code was zero then return, otherwise raise
    CalledProcessError.  The CalledProcessError object will have the
    return code in the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    check_call(["ls", "-l"])
    """
    LOG.debug("%s", list2cmdline(popenargs[0]))
    retcode = call(*popenargs, **kwargs)
    cmd = kwargs.get("args")
    if cmd is None:
        cmd = popenargs[0]
    if retcode:
        raise CalledProcessError(retcode, cmd)
    return retcode


__all__ = [
    'is_lvm_device',
    'lvs',
    'vgs',
    'pvs',
    'lvcreate',
    'lvsnapshot',
    'lvremove',
    'mount',
    'unmount',
    'lvm_dict',
    'lvm_cmd',
]

PVS_ATTRIBUTES = [
    'pv_fmt',
    'pv_uuid',
    'pv_size',
    'dev_size',
    'pv_free',
    'pv_used',
    'pv_name',
    'pv_attr',
    'pv_pe_count',
    'pv_pe_alloc_count',
    'pv_tags',
    # segment info introduces duplicate records
    # (with differing seginfo data)
    #'pvseg_start',
    #'pvseg_size',
    'pe_start',
    'vg_name'
]

VGS_ATTRIBUTES = [
    'vg_fmt',
    'vg_uuid',
    'vg_name',
    'vg_attr',
    'vg_size',
    'vg_free',
    'vg_sysid',
    'vg_extent_size',
    'vg_extent_count',
    'vg_free_count',
    'max_lv',
    'max_pv',
    'pv_count',
    'lv_count',
    'snap_count',
    'vg_seqno',
    'vg_tags'
]

LVS_ATTRIBUTES = [
    'lv_uuid',
    'lv_name',
    'lv_attr',
    'lv_major',
    'lv_minor',
    'lv_kernel_major',
    'lv_kernel_minor',
    'lv_size',
    'seg_count',
    'origin',
    'snap_percent',
    'copy_percent',
    'move_pv',
    'lv_tags',
# segment information break 1:1 mapping
#    'segtype',
#    'stripes',
#    'stripesize',
#    'chunksize',
#   'seg_start',
#   'seg_size',
#   'seg_tags',
#   'devices',
#    'regionsize',
    'mirror_log',
    'modules',
    'vg_name'
]

def is_lvm_device(dev_path):
    """Check if a device path refers to an LVM physical volume
    :param dev_path: path to the device to check
    :returns: True if dev_path is a pv and False otherwise
    """
    args = [
        'pvs',
        '--noheadings',
        '--options', 'pv_name',
    ]
    data = str(lvm_cmd(*args))
    devices = [line.strip() for line in data.splitlines()]
    return dev_path in devices

def pvs(name=None):
    """List available physical volumes and return a dictionary of attributes"""
    args = [
        'pvs',
        '--noheadings',
        '--nosuffix',
        '--separator=,',
        '--units=b',
        '--options', ','.join(PVS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = lvm_cmd(*args)
    return lvm_dict(PVS_ATTRIBUTES, data)

def vgs(name=None):
    """List available volume groups and return a dictionary of attributes"""
    args = [
        'vgs',
        '--noheadings',
        '--nosuffix',
        '--separator=,',
        '--units=b',
        '--options', ','.join(VGS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = lvm_cmd(*args)
    return lvm_dict(VGS_ATTRIBUTES, data)

def lvs(name=None):
    """List available logical volumes and return a dictionary of attributes

    If a name parameter is specified, only matching logical volumes
    will be returned.
    """
    args = [
        'lvs',
        '--noheadings',
        '--nosuffix',
        '--separator=,',
        '--units=b',
        '--options', ','.join(LVS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = lvm_cmd(*args)
    return lvm_dict(LVS_ATTRIBUTES, data)

def lvcreate(lv_name, lv_size, vg_name):
    """Create a new logical volume in the specified volume group"""
    args = [
        'lvcreate',
        '--name', lv_name,
        '--size', str(lv_size),
        vg_name
    ]
    check_call(args)

def lvsnapshot(lv_name, snapshot_name, snapshot_extents):
    """Snapshot an existing logical volume using the specified
    snapshot name and snapshot size.

    snapshot_size should be a valid LVM size string.
    """
    args = [
        'lvcreate',
        '--snapshot',
        '--name', snapshot_name,
        '--extents', str(int(snapshot_extents)),
        lv_name
    ]
    check_call(args)

def lvremove(name):
    """Forcibly remove a logical volume.

    WARNING: This is dangerous and care should be taken before
    calling this method.
    """
    device = os.path.join(os.sep, 'dev', name)
    args = [
        'lvremove',
        '-f',
        device
    ]
    check_call(args)

def mount(device, path, options=None):
    """Mount the specified path or device"""
    #   mount exit status on linux defined by mount(1)
    #   0      success
    #   1      incorrect invocation or permissions
    #   2      system error (out of memory, cannot fork, no more loop devices)
    #   4      internal mount bug or missing nfs support in mount
    #   8      user interrupt
    #   16     problems writing or locking /etc/mtab
    #   32     mount failure
    #   64     some mount succeeded
    if not device:
        raise ValueError("No device specified to mount")
    if not path:
        raise ValueError("No path specified to mount")

    args = [
        'mount',
        device,
        path,
    ]
    if options:
        args.insert(1, options)
        args.insert(1, '-o')

    check_call(*args)

def unmount(path_or_device):
    """Unmount the specified path or device."""
    check_call(['umount', path_or_device])

def lvm_cmd(cmd, *args):
    """Run a LVM command and return the output.

    If a command returns non-zero status, an OSError is raised and the
    errno is set to the returncode of the command.

    For LVM, we also detect the string 'WARNING:' in output, which also
    tends to imply a failure.
    """
    pid = Popen([cmd] + list(args), stdout=PIPE, stderr=PIPE, close_fds=True)
    stdoutdata, stderrdata = pid.communicate()
    if pid.returncode != 0:
        raise CalledProcessError(pid.returncode, cmd)

    # WARNING: Likely means something is seriously broken - either we're not
    # root or the base LVM setup needs fixing. To err on safety we raise
    # an EnvironmentError in this case.
    if "WARNING:" in stderrdata:
        raise CalledProcessError(0, cmd)

    return stdoutdata

def lvm_dict(keys, values):
    """Convert LVM tool output into a dictionary"""
    stream = StringIO(values)
    kwargs = dict(delimiter=',', skipinitialspace=True)
    for row in csv.reader(stream, **kwargs):
        yield dict(zip(keys, row))
