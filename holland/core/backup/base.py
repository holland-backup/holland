"""Standard Holland Backup API classes"""

from holland.core.plugin import load_plugin, ConfigurablePlugin
from holland.core.backup.spool import SpoolError
from holland.core.backup.error import BackupError

class BackupJob(object):
    """A backup job that may be created and passed to a backup manager in order
    to perform a backup"""

    def __init__(self, name, config):
        self.name = name
        self.config = config

    @property
    def plugin(self):
        """Load a plugin from this backup job's config"""
        return self.config['holland:backup']['plugin']

class BackupPlugin(ConfigurablePlugin):
    """Interface that Holland Backup Plugins should conform to"""

    def backup(self, path):
        """Backup to the specified path"""
        raise NotImplementedError()

    def dry_run(self, path):
        """Perform a dry-run backup to the specified path"""
        raise NotImplementedError()

    def backup_info(self):
        """Provide information about this backup"""
        raise NotImplementedError()
