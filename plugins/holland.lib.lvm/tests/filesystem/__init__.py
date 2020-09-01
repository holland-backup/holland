""" Init Module """
import os
import subprocess
import shutil

from holland.lib.lvm.raw import *
from tests.constants import LOOP_DEV, TEST_VG, TEST_LV, IMG_SIZE


def setup(mnt_dir):
    """Setup a simple LVM device to use"""
    os.environ["PATH"] = "/sbin:/usr/sbin:" + os.environ["PATH"]
    size = IMG_SIZE / 512
    img_path = os.path.join(mnt_dir, "test.img")
    subprocess.call("dd if=/dev/zero of=%s count=%d" % (img_path, size), shell=True)
    subprocess.call("losetup %s %s" % (LOOP_DEV, img_path), shell=True)
    subprocess.call("pvcreate %s" % LOOP_DEV, shell=True)
    subprocess.call("vgcreate %s %s" % (TEST_VG, LOOP_DEV), shell=True)
    subprocess.call(
        "lvcreate -L%dK -n %s %s" % ((IMG_SIZE / 2) / 1024, TEST_LV, TEST_VG), shell=True
    )
    subprocess.call("mkfs.ext3 /dev/%s/%s" % (TEST_VG, TEST_LV), shell=True)
    subprocess.call("mount /dev/%s/%s %s" % (TEST_VG, TEST_LV, mnt_dir), shell=True)
    # dd if=/dev/zero of=$staging/foo.img count=N
    # losetup /dev/loopN $staging/foo.img
    # pvcreate /dev/loopN
    # vgcreate $test_vg /dev/loopN
    # lvcreate $test_lv
    # mkfs /dev/$test_vg/$test_lv
    # mount /dev/$test_vg/$test_lv somepath


def teardown(mnt_dir):
    """Remove the previously setup LVM"""
    subprocess.call("umount %s" % mnt_dir, shell=True)
    subprocess.call("vgremove -f %s" % TEST_VG, shell=True)
    subprocess.call("losetup -d %s" % LOOP_DEV, shell=True)
    shutil.rmtree(mnt_dir)
