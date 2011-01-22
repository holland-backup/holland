import logging
from holland.core.backup.base import BackupHook

LOG = logging.getLogger(__name__)

class AutoPurgeFailuresHook(BackupHook):
    def execute(self, job):
        job.store.purge()
        LOG.info("+ Purged failed job %s", job.store.path)

class AutoPurgeHook(BackupHook):
    """Auto-purge old backups when run"""

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
