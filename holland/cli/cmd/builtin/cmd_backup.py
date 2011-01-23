import os, sys
from holland.core import BackupManager, BackupError
from holland.cli.cmd.base import ArgparseCommand, argument

class Backup(ArgparseCommand):
    name = 'backup'
    summary = "Run a backup"
    description = """
    Run a backup
    """
    aliases = ('bk',)
    arguments = [
        argument('--dry-run', '-n', action='store_true'),
        argument('backupset', nargs='*'),
    ]

    def execute(self, namespace):
        if not namespace.backupset:
            self.stderr("Nothing to backup")
            return 1

        backupmgr = BackupManager(self.config['holland']['backup-directory'],
                                  os.path.dirname(self.config.filename or ''))
        for path in namespace.backupset:
            try:
                backupmgr.backup(path, dry_run=namespace.dry_run)
            except BackupError, exc:
                if isinstance(exc.chained_exc, KeyboardInterrupt):
                    self.stderr("Interrupted")
                else:
                    self.stderr("Failed backup '%s': %s", path, exc)
                break
        else:
            return 0
        return 1

    def plugin_info(self):
        return PluginInfo(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            api_version='1.1.0'
        )
