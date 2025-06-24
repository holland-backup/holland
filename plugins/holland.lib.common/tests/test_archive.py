"""
Tetsting Archive lib
"""
import os
import tempfile
import shutil
import unittest
from holland.lib.common.archive import DirArchive, TarArchive, ZipArchive


class TestArchive(unittest.TestCase):
    """Test Archive"""

    tmpdir = None

    def setUp(self):
        """Run before every test"""
        self.__class__.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        """Run after ever test"""
        shutil.rmtree(self.__class__.tmpdir)

    def test_dir_archive(self):
        """Test DirArchive """
        axv = DirArchive(os.path.join(self.__class__.tmpdir, "dir"))
        name_list = []
        for _ in range(1, 16):
            filed, filename = tempfile.mkstemp(dir=self.__class__.tmpdir)
            os.close(filed)
            basename = os.path.basename(filename)
            axv.add_file(filename, basename)
            name_list.append(basename)

        for name in axv.list():
            self.assertTrue(name in name_list)

    def test_tar_archive(self):
        """Test TarArchive """
        axv = TarArchive(os.path.join(self.__class__.tmpdir, "tar"))
        name_list = []

        for _ in range(1, 16):
            filed, filename = tempfile.mkstemp(dir=self.__class__.tmpdir)
            os.close(filed)
            basename = os.path.basename(filename)
            axv.add_file(filename, basename)
            name_list.append(basename)

        for name in axv.list():
            self.assertTrue(name in name_list)

    def test_zip_archive(self):
        """Test ZipArchive """
        axv = ZipArchive(os.path.join(self.__class__.tmpdir, "zip"))
        name_list = []

        for _ in range(1, 16):
            filed, filename = tempfile.mkstemp(dir=self.__class__.tmpdir)
            os.close(filed)
            basename = os.path.basename(filename)
            axv.add_file(filename, basename)
            name_list.append(basename)

        for name in axv.list():
            self.assertTrue(name in name_list)
