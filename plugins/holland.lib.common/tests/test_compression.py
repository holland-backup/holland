""" Test Compression"""
import os
import shutil
import unittest
from tempfile import mkdtemp

from holland.lib.common import compression


class TestCompression(unittest.TestCase):
    """Test Archive"""

    tmpdir = None

    def setUp(self):
        self.__class__.tmpdir = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.__class__.tmpdir)

    def test_lookup_compression(self):
        """Test looking up compression methods"""
        cmd, ext = compression.lookup_compression("gzip")
        self.assertNotEqual(cmd, None)
        self.assertNotEqual(ext, None)

        cmd, ext = compression.lookup_compression("bzip2")
        self.assertNotEqual(cmd, None)
        self.assertNotEqual(ext, None)

        cmd, ext = compression.lookup_compression("lzop")
        self.assertNotEqual(cmd, None)
        self.assertNotEqual(ext, None)

    def test_compression(self):
        """Test Compression methods"""
        # gzip - write it, read it, verify it
        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "gzip_foo"), "w", "gzip"
        )
        filep.write(bytes("foo", "ascii"))
        filep.close()

        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "gzip_foo"), "r", "gzip"
        )
        foo_object = filep.read(3)
        filep.close()

        self.assertTrue(foo_object.decode() == "foo")

        # bzip2 - write it, read it, verify it
        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "bzip2_foo"), "w", "bzip2"
        )
        filep.write(bytes("foo", "ascii"))
        filep.close()

        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "bzip2_foo"), "r", "bzip2"
        )
        foo_object = filep.read(3)
        filep.close()

        self.assertTrue(foo_object.decode() == "foo")

        # gzip - write it, read it, verify it
        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "lzop_foo"), "w", "lzop"
        )
        filep.write(bytes("foo", "ascii"))
        filep.close()

        filep = compression.open_stream(
            os.path.join(self.__class__.tmpdir, "lzop_foo"), "r", "lzop"
        )
        foo_object = filep.read(3)
        filep.close()

        self.assertTrue(foo_object.decode() == "foo")

    def test_compression_bad_mode(self):
        """Test bad mode"""
        filep = compression.open_stream(os.path.join(self.__class__.tmpdir, "foo"), "w", "gzip")
        filep.write(bytes("foo", "ascii"))
        filep.close()
