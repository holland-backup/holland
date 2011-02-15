"""Backup hooks"""

import os
import logging
from datetime import datetime
from holland.core.config import Config
from holland.core.hooks import BaseHook, load_hooks_from_config
from holland.core.backup.base import BackupError
from holland.core.util.fmt import format_bytes

LOG = logging.getLogger(__name__)

class BackupHook(BaseHook):
    """Generic BackupHook"""

    def execute(self, job):
        """Process a backup job event"""
        raise NotImplementedError()

    def plugin_info(self):
        return dict(
            name='internal-hook'
        )
# builtin hooks

class AutoPurgeFailuresHook(BackupHook):
    """Purge failed backups immediately"""

    def execute(self, job):
        """Purge failed backup"""
        LOG.info("+++ Running %s", job.store.path)
        job.store.purge()
        LOG.info("+ Purged failed job %s", job.store.path)

class DryRunPurgeHook(BackupHook):
    """Purge staging directory after a dry-run is complete"""

    def execute(self, job):
        """Purge backup directory for dry-run backup"""
        job.store.purge()
        LOG.info("+ Purged %s after dry-run", job.store.path)

class RotateBackupsHook(BackupHook):
    """Purge old backups when run"""

    def execute(self, job):
        """Process the automated purge policy

        If this runs before starting a new backup it is important to preserve
        the existing backup directory or the plugin will have no where to
        store data.
        """
        retention_count = job.config['holland:backup']['retention-count']
        LOG.info("+ Keep %d backups", retention_count)
        if retention_count == 0:
            LOG.debug("Increasing retention-count to maintain new backup")
            retention_count += 1
        backups, kept, purged = job.store.spool.purge(job.store.name,
                                                      retention_count)
        for backup in purged:
            LOG.info("+ Purged old backup %s", backup.path)
        for backup in kept:
            LOG.info("+ Kept backup %s", backup.path)

class WriteConfigHook(BackupHook):
    """Write config to backup store when called"""

    def execute(self, job):
        """Write a copy of the job config to the backup directory

        This preserves the exact group of settings that were used
        to produce this backup.
        """
        path = os.path.join(job.store.path, 'backup.conf')
        job.config.write(path)
        LOG.info("+ Saved config to %s", path)

class BackupInfoHook(BackupHook):
    """Record information about the backup

    This currently logs start and stop times in ISO8601 format
    in the job.info file as well as the final backup size.
    """
    def __init__(self, name):
        super(BackupInfoHook, self).__init__(name)
        self.initialized = False
        self.config = Config()

    def execute(self, job):
        """Record job info"""
        path = os.path.join(job.store.path, 'job.info')
        if not self.initialized:
            self.initialized = True
            self.config['start-time'] = datetime.now().isoformat()
            self.config.write(path)
        else:
            self.config['stop-time'] = datetime.now().isoformat()
            self.config['actual-size'] = job.store.size()
            self.config.write(path)

class CheckForSpaceHook(BackupHook):
    """Check for available space before starting a backup"""
    def execute(self, job):
        """Estimate the available space from the plugin and abort if
        there does not appear to be enought to successfully complete this
        backup based on the estimate.

        :raises: BackupError if estimated_space > available_space
        """
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

        job_info = Config.read([os.path.join(job.store.path, 'job.info')])
        job_info['estimated-size'] = format_bytes(estimated_bytes)
        if available_bytes < estimated_bytes*estimate_factor:
            raise BackupError("Insufficient space for backup")

def setup_user_hooks(beacon, config):
    """Initialize hooks based on the job config"""
    backup_config = config['holland:backup']
    load_hooks_from_config(backup_config['hooks'], beacon, config)

def setup_builtin_hooks(beacon, config):
    """Connect builtin hook actions with the events they should fire on"""
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
        beacon.before_backup.connect(rotate_backups, weak=False)

def setup_dryrun_hooks(beacon):
    "Setup hook actions that should be run during a dry-run backup"
    # Purge a backup
    hook = DryRunPurgeHook('<internal>')
    beacon.before_backup.connect(hook, sender=None)
    beacon.backup_failure.connect(hook, sender=None)
