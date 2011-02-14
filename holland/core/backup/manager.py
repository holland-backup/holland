"""primary backup api

>>> mgr = BackupManager('/var/spool/holland')
>>> mgr.backup('/etc/holland/backupsets/foo.conf', dry_run=True)
"""

import os
import logging
from holland.core.backup.util import load_backup_plugin, validate_config
from holland.core.backup.spool import BackupSpool, SpoolError, SpoolLockError
from holland.core.backup.job import BackupJob
from holland.core.backup.base import BackupError
from holland.core.config import Config

LOG = logging.getLogger(__name__)

class BackupManager(object):
    """Manage the backup process

    >>> mgr = BackupManager('/var/spool/holland')
    >>> mgr.backup(Config.read(['/etc/holland/backupsets/foo.conf']), dry_run=True)
    """
    def __init__(self, spool_directory):
        self.spool = BackupSpool(spool_directory)

    def backup(self, config, dry_run=False):
        """Run a backup given a backupset name"""
        LOG.info("Backup: %s", config.name)
        validate_config(config)
        name = config.name
        plugin = load_backup_plugin(config)
        LOG.info("+ Found plugin %s", plugin.name)
        try:
            lock = self.spool.lock(name)
        except SpoolLockError, exc:
            raise BackupError("%s appears to already be locked by process %s. "
                              "Is holland already running?" %
                              (os.path.join(self.spool.root, name), exc.pid))
        except SpoolError, exc:
            raise BackupError("There was a problem locking the backup "
                              "directory %s: %s" % (self.spool.root, exc))
        LOG.info("+ Locked spool %s", lock.name)
        store = self.spool.add_store(name)
        LOG.info("+ Initialized backup directory %s", store.path)
        job = BackupJob(plugin, config, store)
        job.run(dry_run)
        lock.close()
        return job

    def purge_backupset(self, name, retention_count=0, dry_run=False):
        """Purge a entire backupset

        :param retention_count: number of recent backups to keep
        :param dry_run: whether to only test what the purge process would do
        :returns: tuple of all_backups, kept_backups, purged_backups
        """
        lock = self.spool.lock(name)
        try:
            return self.spool.purge(name, retention_count, dry_run)
        finally:
            lock.close()

    def purge_backup(self, path, dry_run=False):
        """Purge one backup

        :returns: purged backup
        """
        backupset, instance = path.split('/')
        lock = self.spool.lock(backupset)
        path = os.path.join(self.spool.root, backupset, instance)
        backup = self.spool.load_store(path)
        if dry_run is False:
            backup.purge()
        lock.close()
        return backup

    def cleanup(self, path):
        """Run a plugin's cleanup method"""
        store = self.spool.load_store(path)
        config = Config.read([os.path.join(store.path, 'backup.conf')])
        plugin = load_backup_plugin(config)
        plugin.setup(store)
        plugin.configure(config)
        plugin.cleanup()
