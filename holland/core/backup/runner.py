"""Backup management API"""

import sys
import logging
from holland.core.plugin import default_pluginmgr
from holland.core.dispatch import Signal
from holland.core.backup.error import BackupError

LOG = logging.getLogger(__name__)

class BackupRunner:
    def __init__(self, spool, pluginmgr=None):
        self.spool = spool
        self.pluginmgr = pluginmgr or default_pluginmgr

    def _make_store(self, name):
        try:
            return self.spool.add_store(name)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            raise BackupError("Failed to create backup path",
                              sys.exc_info()[1])

    def _load_plugin(self, job, backupstore):
        try:
            plugin_group = 'holland.backup'
            plugin = self.pluginmgr.load(plugin_group, job.plugin)(backupstore)
            plugin.configure(job.config)
            return plugin
        except:
            raise
        #except:
        #    raise BackupError("Failed to load plugin", sys.exc_info()[1])

    def run(self, job):
        backupstore = self._make_store(job.name)

        try:
            plugin = self._load_plugin(job, backupstore)
            try:
                plugin.setup()
                plugin.estimate_size()
                plugin.backup()
            finally:
                try:
                    plugin.teardown()
                except:
                    pass
        except:
            backupstore.purge()
            exc = sys.exc_info()[0]
            if exc in (SystemExit, KeyboardInterrupt, BackupError):
                raise
            else:
                raise BackupError("Run failed", sys.exc_info()[1])
