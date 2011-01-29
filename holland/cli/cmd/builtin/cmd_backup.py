import os, sys
from holland.core import BackupManager, BackupError, ConfigError
from holland.cli.cmd.base import ArgparseCommand, argument

class Backup(ArgparseCommand):
    name = 'backup'
    summary = "Run a backup"
    description = """
    Run a backup
    """
    aliases = ('bk',)
    arguments = [
        argument('--backup-directory', '-d', dest='directory'),
        argument('--dry-run', '-n', action='store_true'),
        argument('--skip-hooks', action='store_true'),
        argument('backupset', nargs='*'),
    ]

    def __init__(self, *args, **kwargs):
        super(Backup, self).__init__(*args, **kwargs)
        self.parser.set_defaults(
                directory=self.config['holland']['backup-directory'],
                backupset=self.config['holland']['backupsets'],
        )

    def execute(self, namespace):
        backupsets = namespace.backupset

        if not backupsets:
            self.stderr("Nothing to backup")
            return 1

        backupmgr = BackupManager(namespace.directory)

        for name in backupsets:
            try:
                config = self.config.load_backupset(name)
            except ConfigError, exc:
                self.stderr("Failed to load backupset config %s: %s",
                            name, exc)
                return 1

            if namespace.skip_hooks:
                try:
                    config['holland:backup']['hooks'] = 'no'
                except KeyError:
                    # ignore bad configs - this gets caught by the
                    # BackupManager during config validation
                    pass

            try:
                backupmgr.backup(config, dry_run=namespace.dry_run)
            except BackupError, exc:
                if isinstance(exc.chained_exc, KeyboardInterrupt):
                    self.stderr("Interrupted")
                else:
                    self.stderr("Failed backup '%s': %s", config.name, exc)
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
