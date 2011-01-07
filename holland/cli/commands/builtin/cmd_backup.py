import os, sys
from holland.core import BackupManager, BackupJob, BackupError, BackupSpool
from holland.cli.commands.base import ArgparseCommand, argument
from holland.cli.config import load_backup_config

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
        spool = BackupSpool(self.config['holland']['backup-directory'])
        backupmgr = BackupManager()
        if not self.config.filename:
            base_path = os.getcwd()
        else:
            base_path = os.path.dirname(self.config.filename)

        if namespace.dry_run:
            run_backup = backupmgr.run
        else:
            run_backup = backupmgr.dry_run

        if not namespace.backupset:
            self.stderr("Nothing to backup")
            return 1

        for path in namespace.backupset:
            if not os.path.isabs(path):
                path = os.path.join(base_path, path)
            if not path.endswith('.conf'):
                path += '.conf'
            try:
                config = load_backup_config(path)
            except IOError, exc:
                self.stderr("Failed to load config %s: %s",
                            path, exc)
                return 1
            try:
                job = BackupJob(name, config, spool)
                run_backup(job)
                print "OKAY?"
            except BackupError, exc:
                self.stderr("Failed backup '%s': %s", name, exc)
                print "ARGH"
                return 1
        else:
            return 0

        # should never reach here
        return 1
