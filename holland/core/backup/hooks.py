"""Backup hooks"""

import os
import logging
from datetime import datetime
from holland.core.hooks import BaseHook, load_hooks_from_config
from holland.core.backup.base import BackupError
from holland.core.util.fmt import format_bytes

LOG = logging.getLogger(__name__)

class BackupHook(BaseHook):
    def execute(self, job):
        """Process a backup job event"""

# builtin hooks

class AutoPurgeFailuresHook(BackupHook):
    def execute(self, job):
        LOG.info("+++ Running %s", job.store.path)
        job.store.purge()
        LOG.info("+ Purged failed job %s", job.store.path)

class DryRunPurgeHook(BackupHook):
    def execute(self, job):
        job.store.purge()
        LOG.info("+ Purged %s after dry-run", job.store.path)

class RotateBackupsHook(BackupHook):
    """Purge old backups when run"""

    def execute(self, job):
        retention_count = job.config['holland:backup']['backups-to-keep']
        LOG.info("+ Keep %d backups", retention_count)
        for backup in job.store.oldest(retention_count):
            backup.purge()
            LOG.info("+ Purged old backup %s", job.store.path)

class WriteConfigHook(BackupHook):
    """Write config to backup store when called"""

    def execute(self, job):
        path = os.path.join(job.store.path, 'backup.conf')
        job.config.write(path)
        LOG.info("+ Saved config to %s", path)

class BackupInfoHook(BackupHook):
    def __init__(self, name):
        super(BackupInfoHook, self).__init__(name)
        self.initialized = False

    def execute(self, job):
        if not self.initialized:
            config = job.config.setdefault('holland:backup:run', {})
            self.initialized = True
            config['start-time'] = datetime.now().isoformat()
        else:
            config = job.config['holland:backup:run']
            config['stop-time'] = datetime.now().isoformat()

class CheckForSpaceHook(BackupHook):

    def execute(self, job):
        LOG.info("+ Estimating backup size")
        estimated_bytes = job.plugin.estimate()
        available_bytes = job.store.spool_capacity()
        estimate_factor = job.config['holland:backup']['estimated-size-factor']

        LOG.info("+ Plugin estimated backup size of %s",
                format_bytes(estimated_bytes))
        LOG.info("+ Adjusted plugin estimated by %.2f%% to %s",
                 estimate_factor*100,
                 format_bytes(estimated_bytes*estimate_factor))
        LOG.info("+ Spool directory %s has %s available",
                 job.store.path, format_bytes(available_bytes))

        job.config['holland:backup:run']['estimated-size'] = format_bytes(estimated_bytes)
        if available_bytes < estimated_bytes*estimate_factor:
            raise BackupError("Insufficient space for backup")

def setup_user_hooks(beacon, config):
    """Initialize hooks based on the job config"""
    backup_config = config['holland:backup']
    for event, signal in beacon.iteritems():
        for hook in load_hooks_from_config(backup_config[event], config):
            signal.connect(hook, sender=None, weak=False)

def setup_builtin_hooks(beacon, config):
    config_writer = WriteConfigHook('<internal>')
    estimation = CheckForSpaceHook('<internal>')
    backup_info = BackupInfoHook('<internal>')

    beacon.before_backup.connect(backup_info, weak=False)
    beacon.before_backup.connect(estimation, weak=False)
    beacon.before_backup.connect(config_writer, weak=False)

    beacon.after_backup.connect(backup_info, weak=False)
    beacon.after_backup.connect(config_writer, weak=False)

    config = config['holland:backup']
    if config['auto-purge-failures']:
        purge_failures_hook = AutoPurgeFailuresHook('<internal>')
        beacon.backup_failure.connect(purge_failures_hook, weak=False)

    if config['purge-policy'] == 'after-backup':
        rotate_backups = RotateBackupsHook('<internal>')
        beacon.after_backup.connect(rotate_backups, weak=False)
    elif config['purge-policy'] == 'before-backup':
        rotate_backups = RotateBackupsHook('<internal>')
        beacon.after_backup.connect(rotate_backups, weak=False)

def setup_dryrun_hooks(beacon, config):
    "Setup hook actions that should be run during a dry-run backup"
    # Purge a backup
    hook = DryRunPurgeHook('<internal>')
    beacon.before_backup.connect(hook, sender=None)
    beacon.backup_failure.connect(hook, sender=None)
