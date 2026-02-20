"""Test for sqlite plugin"""
import os
import shutil
import time
import unittest
from tempfile import mkdtemp

from configobj import ConfigObj

from holland.backup.sqlite import SQLitePlugin
from holland.lib.common.which import which


class MockConfig(ConfigObj):
    """Mock Config Class"""

    def validate_config(self, *args, **kw):
        """Pass"""


class BackupError(Exception):
    """Mock BackupError"""


class TestSQLite(unittest.TestCase):
    """Test SQLite Plugin"""

    config = {}

    @classmethod
    def setUpClass(cls):
        "set up test fixtures"
        cls.config = MockConfig()
        cls.config["sqlite"] = {
            "databases": [os.path.join(os.path.dirname(__file__), "sqlite.db")]
        }
        cls.config["compression"] = {"method": "gzip", "inline": "yes", "level": 1}

        # Disabling lint as unittest was failing on the BackupError exception
        try:
            cls.config["sqlite"]["binary"] = which("sqlite")
        except:  # pylint: disable-msg=W0702
            cls.config["sqlite"]["binary"] = which("sqlite3")

        cls.config["tmpdir"] = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.config["tmpdir"]):
            shutil.rmtree(cls.config["tmpdir"])

    def test_sqlite_dry_run(self):
        """Test Dry run"""
        name = "sqlite/" + time.strftime("%Y%m%d_%H%M%S")
        dry_run = True
        plugin = SQLitePlugin(
            name, self.__class__.config, self.__class__.config["tmpdir"], dry_run
        )
        plugin.backup()

    def test_sqlite_plugin(self):
        """Test backup"""
        name = "sqlite/" + time.strftime("%Y%m%d_%H%M%S")
        dry_run = False
        plugin = SQLitePlugin(
            name, self.__class__.config, self.__class__.config["tmpdir"], dry_run
        )
        self.assertEqual(plugin.estimate_backup_size(), 2048)
        plugin.backup()

    def test_sqlite_info(self):
        """Test info"""
        name = "sqlite/" + time.strftime("%Y%m%d_%H%M%S")
        dry_run = False
        plugin = SQLitePlugin(
            name, self.__class__.config, self.__class__.config["tmpdir"], dry_run
        )
        self.assertTrue(isinstance(plugin.info(), str))
