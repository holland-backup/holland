"""Command to run a holland backup"""
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
        "Run the backup command"
        backupsets = namespace.backupset

        if not backupsets:
            self.stderr("Nothing to backup")
            return 1

        backupmgr = BackupManager(namespace.directory)

        skip_hooks = namespace.skip_hooks
        dry_run = namespace.dry_run

        for name in backupsets:
            try:
                self.run_backup(name, backupmgr,
                                skip_hooks=skip_hooks,
                                dry_run=dry_run)
            except (KeyboardInterrupt, SystemExit):
                raise
            except (ConfigError, BackupError), exc:
                self.stderr("Backup '%s' failed: %s", name, exc)
                break
        else:
            return 0
        return 1

    def run_backup(self, name, backupmgr, skip_hooks=False, dry_run=False):
        "Run a single backup"
        config = self.config.load_backupset(name)
        if skip_hooks:
            try:
                config['holland:backup']['hooks'] = 'no'
            except KeyError:
                # ignore bad configs - this gets caught by the
                # BackupManager during config validation
                pass
        backupmgr.backup(config, dry_run=dry_run)

    #@classmethod
    def plugin_info(cls):
        "Backup command plugin info"
        return dict(
            name=cls.name,
            summary=cls.summary,
            description=cls.description,
            author='Rackspace',
            version='1.1.0',
            api_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)
