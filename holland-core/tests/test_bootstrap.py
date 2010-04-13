import os
import shutil
import tempfile
import unittest
from holland.core.config import setup_config
from holland.core.log import clear_root_handlers
from holland.core.util.bootstrap import bootstrap, setup_logging
from holland.core.util.fmt import format_loglevel
from optparse import OptionParser

class TestBootstrap(unittest.TestCase):
    def setUp(self):
        clear_root_handlers()
        # This is tested in test_config.py
        self.tmpdir = tempfile.mkdtemp()
        log_file = os.path.join(self.tmpdir, 'holland.log')
        test_cfg = """
        [holland]
        plugin_dirs = /usr/share/holland/plugins
        backupsets = default
        umask = 0007
        path = /bin:/usr/bin:/usr/local/bin:/usr/local/sbin:/usr/local/mysql/bin

        [logging]
        level = critical
        filename = %s
        """ % (log_file)
        path = os.path.join(self.tmpdir, 'holland.conf')
        open(path, 'w').write(test_cfg)
        setup_config(path)

    def test_log_level(self):
        """
        Test for issue #1323 - ensure log level is set according to holland.conf
        """
        p = OptionParser()
        p.add_option('--verbose', '-v', action='store_true', default=False)
        p.add_option('--quiet', '-q', action='store_true', default=True)
        p.add_option('--log-level', '-l', type='choice',
                     choices=['critical', 'error', 'warning', 'info', 'debug'])
        opts, args = p.parse_args(['test'])
        setup_logging(opts)
        import logging
        self.assertEquals(logging.getLogger().getEffectiveLevel(), logging.CRITICAL)

    def test_backupset(self):
        pass

    def test_provider(self):
        pass

    def tearDown(self):
        pass
