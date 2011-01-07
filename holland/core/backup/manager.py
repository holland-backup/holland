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

class BackupManager(AbstractBackupManager):
    """BackupManager that manages a spool"""
    def __init__(self):
        AbstractBackupManager.__init__(self)
        self.pre_backup = Signal()
        self.post_backup = Signal()

    def dry_run(self, job):
        """Dry-run through the backup process

        :param job: ``holland.core.backup.BackupJob`` instance
        :raises BackupError:
        """
        plugin = self._setup(job)
        try:
            self.dry_run(plugin)
        finally:
            try:
                self.finish(plugin)
            except:
                pass

    def run(self, job):
        """Run a backup job

        :param job: ``holland.core.backup.BackupJob`` instance
        :raises BackupError: on failure
        """
        plugin = self._setup(job)
        try:
            self.backup(plugin)
        finally:
            try:
                self.finish(plugin)
            except:
                pass

    def _setup(self, job):
        "Setup a plugin for a backup run"
        plugincls = self._load_plugin(job)
        plugin = self._init_plugin(plugincls, job)
        self.setup_plugin(plugin)
        return plugin

    #@staticmethod
    def _load_plugin(job):
        """Load the plugin associated with the given job

        :raises: BackupError on error
        """
        name = job.config['holland:backup']['plugin']
        return load_plugin('holland.backup', name)
    _load_plugin = staticmethod(_load_plugin)

    #@staticmethod
    def _init_plugin(plugincls, job):
        """Initialize a plugin by calling its constructor"""
        try:
            return plugincls(job.name)
        except:
            exc = sys.exc_info()[1]
            raise BackupError(exc)
    _init_plugin = staticmethod(_init_plugin)

    def _setup_plugin(self, plugin):
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
    def _backup(plugin, path):
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
    _backup = staticmethod(_backup)

    def _finish(self, plugin):
        "Signal the finale of a plugin's backup lifecycle"
        plugin.teardown()
        self.post_backup.send_robust(sender=self, plugin=plugin)
