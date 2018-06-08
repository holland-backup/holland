import os
import shutil
import tempfile
import unittest
from holland.core.config import hollandcfg, setup_config

class TestHollandConfig(unittest.TestCase):
    def setUp(self):
        test_cfg = """
        [holland]
        plugin_dirs = /usr/share/holland/plugins
        backupsets = default
        umask = 0007
        path = /bin:/usr/bin:/usr/local/bin:/usr/local/sbin:/usr/local/mysql/bin

        [logging]
        level = info
        filename = /dev/null
        """
        self.tmpdir = tempfile.mkdtemp()
        path = os.path.join(self.tmpdir, 'holland.conf')
        open(path, 'w').write(test_cfg)
        setup_config(path)

    def test_globalconfig(self):
        import logging
        cfgentry_tests = {
            'holland.plugin-dirs' : ['/usr/share/holland/plugins'],
            'holland.umask' : int('0007', 8),
            'holland.path' : '/bin:/usr/bin:/usr/local/bin:/usr/local/sbin:/usr/local/mysql/bin',

            'logging.level' : logging.INFO,
            'logging.filename' : '/dev/null'
        }

        for key, value in list(cfgentry_tests.items()):
            self.assertEqual(hollandcfg.lookup(key), value)

    def test_backupset(self):
        pass

    def test_provider(self):
        pass

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
