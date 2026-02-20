"""
Define untily test module
"""

import os
import signal
import unittest

from holland.lib.lvm.util import format_bytes, getdevice, getmount, parse_bytes, relpath


class TestUtilityMethods(unittest.TestCase):
    """Test Utility"""

    def test_format_bytes(self):
        """format_bytes"""
        self.assertEqual(format_bytes(1024), "1.00KB")
        self.assertEqual(format_bytes(0), "0.00Bytes")

    def test_getmount(self):
        """getmount"""
        self.assertEqual(getmount("/"), "/")
        self.assertEqual(getmount("/foobarbaz"), "/")

    def test_getdevice(self):
        """get root fs, and test getdevice"""
        dev = None
        filep = open("/etc/mtab", "r")
        for line in filep:
            row = line.split()
            if row[1] == "/":
                dev = row[0]
        filep.close()
        self.assertEqual(getdevice("/"), dev)
        self.assertEqual(getdevice("/foobarbaz"), None)

    def test_relpath(self):
        """repath"""
        self.assertRaises(ValueError, relpath, "")
        self.assertEqual(relpath("/foo/bar/baz", "/foo/bar"), "baz")
        self.assertEqual(relpath("/foo/bar/", "/foo/bar/"), os.curdir)

    def test_signalmanager(self):
        """test siginit"""
        unittest.installHandler()
        unittest.removeHandler()
        self.assertRaises(KeyboardInterrupt, os.kill, os.getpid(), signal.SIGINT)

    def test_parsebytes(self):
        """parse_bytes"""
        # bytes without units should be interpretted as MB
        parsed = parse_bytes("1024")
        self.assertEqual(parsed, 1024**3)
        # this should not be bytes
        self.assertTrue(parsed > 1024)

        parsed = parse_bytes("1024G")
        self.assertEqual(parsed, 1024**4)
