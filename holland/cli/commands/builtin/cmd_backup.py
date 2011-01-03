import os, sys
from holland.core import BackupManager, SpoolManager
from holland.cli.commands.base import ArgparseCommand, argument

class Backup(ArgparseCommand):
    name = 'backup'
    summary = "Run a backup"
    description = """
    Run a backup
    """
    aliases = ('bk',)
    arguments = [
        argument('--dry-run', '-n'),
        argument('backupset', nargs='*'),
    ]

    def execute(self, namespace):
        spool = SpoolManager(self.config['holland']['backup-directory'])
        backup_mgr = BackupManager(spool)
        base_path = os.path.dirname(self.config.filename)

        if namespace.dry_run:
            run_backup = backup_mgr.run
        else:
            run_backup = backup_mgr.dry_run

        for name in namespace.backupsets:
            try:
                path = os.path.join(base_path, name)
                if not path.endswith('.conf'):
                    path += '.conf'
                config = load_config(path)
                job = BackupJob(name, config, spool.next())
                run_backup(job)
            except BackupError, exc:
                self.stderr("Failed backup '%s': %s", name, exc)
                return 1
        else:
            return 0

        # should never reach here
        return 1
