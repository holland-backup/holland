import os, sys
import time
import errno
import fcntl
import logging
from holland.core.command import Command, option, run
from holland.core.backup import BackupRunner, BackupError
from holland.core.exceptions import BackupError
from holland.core.config import hollandcfg, ConfigError
from holland.core.spool import spool
from holland.core.util.fmt import format_interval

LOG = logging.getLogger(__name__)

class Backup(Command):
    """${cmd_usage}

    Backup the specified backupsets or all
    active backupsets specified in holland.conf

    ${cmd_option_list}

    """

    name = 'backup'

    aliases = [
        'bk'
    ]

    options = [
        option('--abort-immediately', action='store_true',
                help="Abort on the first backupset that fails."),
        option('--dry-run', '-n', action='store_true',
                help="Print backup commands without executing them."),
        option('--no-lock', '-f', action='store_true',
                help="Run even if another copy of Holland is running.")
    ]

    description = 'Run backups for active backupsets'

    def run(self, cmd, opts, *backupsets):
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]

        if not backupsets:
            LOG.info("Nothing to backup")
            return 1

        runner = BackupRunner(spool)
        purge_mgr = PurgeManager()

        runner.register_cb('pre-backup', purge_mgr)
        runner.register_cb('post-backup', purge_mgr)
        runner.register_cb('backup-failure', purge_backup)

        LOG.info("---> Starting backup run <---")
        for name in backupsets:
            try:
                config = hollandcfg.backupset(name)
            except IOError, exc:
                LOG.error("Could not load backupset '%s': %s", name, exc)
                break
            try:
                runner.backup(name, config, opts.dry_run)
            except BackupError, exc:
                LOG.error("Backup failed: %s", exc)
            except ConfigError, exc:
                break
        else:
            return 0
        LOG.info("---> Ending backup run <---")
        return 1

def purge_backup(event, entry):
    if entry.config['holland:backup']['auto-purge-failures']:
        entry.purge()
        LOG.info("Purged failed backup: %s", entry.name)
    else:
        LOG.info("Failed backup not purged due to purge-failed-backups setting")

class PurgeManager(object):
    def __call__(self, event, entry):
        purge_policy = entry.config['holland:backup']['purge-policy']

        if event == 'pre-backup' and purge_policy != 'before-backup':
            return
        if event == 'post-backup' and purge_policy != 'after-backup':
            return

        backupset = spool.find_backupset(entry.backupset)
        if not backupset:
            LOG.info("Nothing to purge")
            return

        retention_count = entry.config['holland:backup']['backups-to-keep']
        retention_count = int(retention_count)
        if event == 'post-backup' and retention_count == 0:
            # Always maintain latest backup
            LOG.warning("!! backups-to-keep set to 0, but "
                        "purge-policy = after-backup. This would immediately "
                        "purge all backups which is probably not intended. "
                        "Setting backups-to-keep to 1")
            retention_count = 1
        self.purge_backupset(backupset, retention_count)

    def purge_backupset(self, backupset, retention_count):
        purge_count = 0
        for backup in backupset.purge(retention_count):
            purge_count += 1
            LOG.info("Purged %s", backup.name)
        
        if purge_count == 0:
            LOG.info("No backups purged")
        else:
            LOG.info("%d backups purged", purge_count)
