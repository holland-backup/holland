"""Purge backups"""

from holland.core import BackupManager, ConfigError
from holland.core.util.fmt import format_bytes
from holland.cli.cmd.base import ArgparseCommand, argument

class Purge(ArgparseCommand):
    """Purge backup command"""
    name = 'purge'
    summary = 'Purge a backup'
    description = """
    Purge a backup
    """

    arguments = [
        argument('--all', const=0,
                 action='store_const',
                 dest='retention_count'),
        argument('--retention-count', default=None,
                 type=int),
        argument('--dry-run', '-n', dest='dry_run', default=True),
        argument('--force', action='store_false', dest='dry_run'),
        argument('--execute', dest='dry_run', action='store_false'),
        argument('--backup-directory', '-d'),
        argument('backups', nargs='*'),
    ]

    def create_parser(self):
        parser = ArgparseCommand.create_parser(self)
        parser.set_defaults(
            backup_directory=self.config['holland']['backup-directory']
        )
        return parser

    def execute(self, namespace, parser):
        "Purge a backup"

        if not namespace.backup_directory:
            self.stderr("No backup-directory defined.")
            return 1

        mgr = BackupManager(namespace.backup_directory)
        if namespace.dry_run:
            self.stderr("Running in dry-run mode. "
                        "Use --force to run a real purge")

        for name in namespace.backups:
            if '/' in name:
                mgr.purge_backup(name, dry_run=namespace.dry_run)
            else:
                retention_count = namespace.retention_count
                if retention_count is None:
                    retention_count = self._retention_count(name)
                self.stderr("Retention count: %r", retention_count)
                backups, kept, purged = mgr.purge_backupset(name,
                                                            retention_count,
                                                            dry_run=namespace.dry_run)
                self.stderr("Total backups:  %d", len(backups))
                self.stderr("Kept backups:   %d", len(kept))
                self.stderr("Purged backups: %d", len(purged))
                for backup in kept:
                    self.stderr("  + %s [%s]", backup.path,
                                format_bytes(backup.size()))
                for backup in purged:
                    self.stderr("  - %s [%s]", backup.path,
                                format_bytes(backup.size()))
        return 0

    def _retention_count(self, backupset):
        try:
            config = self.config.load_backupset(backupset)['holland:backup']
            return config['retention-count']
        except ConfigError:
            self.stderr("Failed to load backupset config for %s. "
                        "Defaulting to retention-count = 1", backupset)
            return 1

    def plugin_info(self):
        """Purge plugin info"""
        return dict(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
