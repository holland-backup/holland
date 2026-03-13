"""
Test Error module
"""
import unittest

from holland.lib.lvm.errors import LVMCommandError


class TestErrors(unittest.TestCase):
    """Test Errors"""

    def test_errors(self):
        """LVMCommandError"""
        exc = LVMCommandError("cmd", -1, "error message")
        self.assertEqual(exc.cmd, "cmd")
        self.assertEqual(exc.status, -1)
        self.assertEqual(exc.error, "error message")
