"""Backup management API"""

import sys
from holland.core.dispatch import Signal
from holland.core.backup.error import BackupError

class BackupRunner:
    def __init__(self, spool, pluginmgr=None):
        self.spool = spool
        self.pluginmgr = pluginmgr or defaultpluginmgr

    def _make_store(self, name):
        try:
            return spool.add_store(name)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            raise BackupError("Failed to create backup path", exc)

    def _load_plugin(self, job):
        try:
            plugin_group = 'holland.backup'
            plugin = self.pluginmgr.load(plugin_group, job.plugin)(job.name)
            plugin.configure(job.config)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            raise BackupError("Failed to load plugin", sys.exc_info()[1])

    def run(self, job):
        backupstore = self._make_store(job.name)

        try:
            plugin = self._load_plugin(job)
            try:
                plugin.setup()
                plugin.estimate_size()
                plugin.backup()
            finally:
                plugin.teardown()
        except:
            backupstore.purge()
            raise
