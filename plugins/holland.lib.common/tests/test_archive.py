# pylint: skip-file

import os
import shutil
import tempfile
from nose.tools import *
from holland.lib.archive import *

def setup_func():
    global tmpdir
    tmpdir = tempfile.mkdtemp()

def teardown_func():
    global tmpdir
    shutil.rmtree(tmpdir)

@with_setup(setup_func, teardown_func)
def test_dir_archive():
    global tmpdir
    axv = DirArchive(os.path.join(tmpdir, 'dir'))
    name_list = []
    for num in range(1, 16):
        fd, filename = tempfile.mkstemp(dir=tmpdir)
        os.close(fd)
        basename = os.path.basename(filename)
        axv.add_file(filename, basename)
        name_list.append(basename)

    for name in axv.list():
        ok_(name in name_list)

@with_setup(setup_func, teardown_func)
def test_tar_archive():
    global tmpdir
    axv = TarArchive(os.path.join(tmpdir, 'tar'))
    name_list = []

    for num in range(1, 16):
        fd, filename = tempfile.mkstemp(dir=tmpdir)
        os.close(fd)
        basename = os.path.basename(filename)
        axv.add_file(filename, basename)
        name_list.append(basename)

    for name in axv.list():
        ok_(name in name_list)

@with_setup(setup_func, teardown_func)
def test_zip_archive():
    global tmpdir
    axv = ZipArchive(os.path.join(tmpdir, 'zip'))
    name_list = []

    for num in range(1, 16):
        fd, filename = tempfile.mkstemp(dir=tmpdir)
        os.close(fd)
        basename = os.path.basename(filename)
        axv.add_file(filename, basename)
        name_list.append(basename)

    for name in axv.list():
        ok_(name in name_list)
