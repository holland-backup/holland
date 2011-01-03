"""Backup management API"""

import sys
from holland.core.plugin import load_plugin
from holland.core.dispatch import Signal
from holland.core.backup.error import BackupError

class AbstractBackupManager(object):
    "Interface a BackupManager should implement"

    def run(self, job):
        """Run a backup job"""
        raise NotImplementedError()

    def dry_run(self, job):
        """Test a backup job"""
        raise NotImplementedError()

class DefaultBackupManager(AbstractBackupManager):
    """BackupManager that manages a spool"""
    def __init__(self):
        AbstractBackupManager.__init__(self)
        self.pre_backup = Signal()
        self.post_backup = Signal()

    def dry_run(self, job):
        plugin = self.setup(job)
        try:
            self.dry_run(plugin)
        finally:
            try:
                self.finish(plugin)
            except:
                pass

    def run(self, job):
        """Run a backup job

        :raises: BackupError on failure
        """
        plugin = self.setup(job)
        try:
            self.backup(plugin)
        finally:
            try:
                self.finish(plugin)
            except:
                pass

    def setup(self, job):
        "Setup a plugin for a backup run"
        plugincls = self.load_plugin(job)
        plugin = self.init_plugin(plugincls, job)
        self.setup_plugin(plugin)
        return plugin

    #@staticmethod
    def load_plugin(job):
        """Load the plugin associated with the given job

        :raises: BackupError on error
        """
        name = job.config['holland:backup']['plugin']
        plugincls = load_plugin('holland.backup', name)
        return plugincls(job)
    load_plugin = staticmethod(load_plugin)

    #@staticmethod
    def init_plugin(plugincls, job):
        """Initialize a plugin by calling its constructor"""
        try:
            return plugincls(job)
        except:
            exc = sys.exc_info()[1]
            raise BackupError(exc)
    init_plugin = staticmethod(init_plugin)

    def setup_plugin(self, plugin):
        """Run through a plugin's setup method

        :raises: BackupError when plugin.setup() raises an unexpected runtime
                 error
        """
        try:
            plugin.setup()
        except NotImplementedError:
            pass
        except:
            exc = sys.exc_info()[1]
            raise BackupError(exc)
        self.pre_backup.send_robust(sender=self, plugin=plugin)

    #@staticmethod
    def backup(plugin, path):
        """Run a plugin's backup() method

        :raises: BackupError on failure
        """
        try:
            plugin.backup(path)
        except BackupError:
            raise
        except:
            exc = sys.exc_info()[1]
            raise BackupError(exc)
    backup = staticmethod(backup)

    def finish(self, plugin):
        "Signal the finale of a plugin's backup lifecycle"
        plugin.teardown()
        self.post_backup.send_robust(sender=self, plugin=plugin)
