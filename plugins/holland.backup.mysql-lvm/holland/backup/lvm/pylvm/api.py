"""LVM command API"""

import os
import csv
import errno
import string
import tempfile
import textwrap
import logging
from subprocess import Popen, PIPE, STDOUT, list2cmdline
from cStringIO import StringIO
import fmt

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
    'run_cmd',
    'LVMError'
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

class LVMError(EnvironmentError):
    pass

def which(cmd, search_path=None):
    """Find the canonical path for a command"""
    if not search_path:
        search_path = os.getenv('PATH', '').split(':')

    logging.debug("Using search_path: %r", search_path)
    for name in search_path:
        cmd_path = os.path.join(name, cmd)
        if os.access(cmd_path, os.X_OK):
            return cmd_path
    else:
        raise LVMError(errno.ENOENT, "%r: command not found" % cmd)

def is_lvm_device(dev_path):
    args = [
        'pvs',
        '--noheadings',
        '-o', 'pv_name',
    ]
    data = run_cmd(*args)
    devices = map(string.strip, data.splitlines())
    return dev_path in devices

def pvs(name=None):
    """List available physical volumes and return a dictionary of attributes"""
    args = [
        'pvs',
        '--noheadings',
        '--nosuffix',
        '--separator=,',
        '--units=b',
        '-o', ','.join(PVS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = run_cmd(*args)
    return lvm_dict(PVS_ATTRIBUTES, data)

def vgs(name=None):
    """List available volume groups and return a dictionary of attributes"""
    args = [
        'vgs',
        '--noheadings',
        '--nosuffix',
        '--separator=,',
        '--units=b',
        '-o', ','.join(VGS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = run_cmd(*args)
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
        '-o', ','.join(LVS_ATTRIBUTES)
    ]
    if name:
        args.append(name)
    data = run_cmd(*args)
    return lvm_dict(LVS_ATTRIBUTES,data)

def lvcreate(lv_name, lv_size, vg_name):
    """Create a new logical volume in the specified volume group"""
    args = [
        'lvcreate',
        '--name', lv_name,
        '--size', fmt.validate_size(lv_size),
        vg_name
    ]
    run_cmd(*args)

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
    run_cmd(*args)

def lvremove(name):
    """Forcibly remove a logical volume.

    WARNING: This is dangerous and care should be taken before
    calling this method.
    """
    device = os.path.join(os.sep, 'dev', name)
    if not os.path.exists(device):
        raise LVMError('Logical Volume %r does not exist' % device, errno.ENOENT)
    args = [
        'lvremove',
        '-f',
        name
    ]
    run_cmd(*args)

def mount(device, path):
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
    logging.debug("mount(%r, %r)", device, path)
    if not device:
        raise LVMError("No device specified to mount")
    if not path:
        raise LVMError("No path specified to mount")

    run_cmd('mount', device, path)

def unmount(path_or_device):
    """Unmount the specified path or device."""
    run_cmd('umount', path_or_device)

def run_cmd(cmd, *args):
    """Run a LVM command and return the output.

    If a command returns non-zero status, an OSError is raised and the
    errno is set to the returncode of the command.

    For LVM, we also detect the string 'WARNING:' in output, which also
    tends to imply a failure.
    """
    cmd = which(cmd)

    logging.debug("Running %s", list2cmdline([cmd] + list(args)))
    pid = Popen([cmd] + list(args), stdout=PIPE, stderr=PIPE, close_fds=True)
    stdoutdata, stderrdata = pid.communicate()
    if pid.returncode != 0:
        raise LVMError(
                      pid.returncode,
                      str(stderrdata).strip(),
                      cmd
                     )

    # WARNING: Likely means something is seriously broken - either we're not
    # root or the base LVM setup needs fixing. To err on safety we raise
    # an EnvironmentError in this case.
    if "WARNING:" in stderrdata:
        raise LVMError(0,
                      str(stderrdata).strip(),
                      cmd
                     )

    return stdoutdata

def lvm_dict(keys, values):
    """Convert LVM tool output into a dictionary"""
    stream = StringIO(values)
    kwargs = dict(delimiter=',', skipinitialspace=True)
    for row in csv.reader(stream, **kwargs):
        logging.debug("row = %r", zip(keys, row))
        logging.debug("dict= %r", dict(zip(keys, row)))
        yield dict(zip(keys, row))
