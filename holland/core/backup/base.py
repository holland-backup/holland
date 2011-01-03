"""Standard Holland Backup API classes"""

from holland.core.plugin import load_plugin, ConfigurablePlugin
from holland.core.spool import SpoolError
from holland.core.backup.error import BackupError

class BackupJob(object):
    """A backup job that may be created and passed to a backup manager in order
    to perform a backup"""

    def __init__(self, name, config, spool):
        self.name = name
        self.config = config
        self.spool = spool

    def load_plugin(self):
        """Load a plugin from this backup job's config"""
        name = self.config['holland:backup']['plugin']
        return load_plugin('holland:backup', name)

    def make_path(self):
        "Create a path for this backup job"
        try:
            return self.spool.add(self.name)
        except SpoolError, exc:
            raise BackupError("Failed to create backup path: %s" % exc)

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
