""" Example plugin test """

import time
import unittest

from holland.backup.example import ExamplePlugin


# Config mock, so we don't have to import holland.core
class MockConfig:
    """Example mock configuration object"""

    def validate(self, spec):
        """Example validation method"""

    def validate_config(self, spec):
        """Example validation method"""


class TestExample(unittest.TestCase):
    """Test Sample"""

    def test_example_plugin(self):
        """Example driver function"""
        name = "example/" + time.strftime("%Y%m%d_%H%M%S")
        target_directory = "/tmp/example_backup/"
        config = MockConfig()
        dry_run = False

        plugin = ExamplePlugin(name, config, target_directory, dry_run)
        self.assertEqual(plugin.estimate_backup_size(), 0)
        plugin.backup()

        dry_run = True

        plugin = ExamplePlugin(name, config, target_directory, dry_run)
        plugin.backup()

        self.assertTrue(isinstance(plugin.info(), str))
