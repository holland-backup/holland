# pylint: skip-file

import os
import holland.backup.lvm.pylvm.api
from . import lvm_helper

def setup():
    if os.geteuid() != 0:
        raise OSError("LVM tests must be run as root.")

    if not 'VGNAME' in os.environ:
        raise EnvironmentError("You must specify a VGNAME environment variable to run these tests.")

    if 'LVMPATH' in os.environ:
        path = os.getenv('PATH', '')
        path = ':'.join([path, os.getenv('LVMPATH')])
        os.environ['PATH'] = path

def teardown():
    lvm_helper.teardown()
