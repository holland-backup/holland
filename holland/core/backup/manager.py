"""primary backup api

>>> mgr = BackupManager('/var/spool/holland')
>>> mgr.backup('/etc/holland/backupsets/foo.conf', dry_run=True)
"""

import os, sys
import logging
from holland.core.backup.util import validate_backup_config, load_backup_plugin
from holland.core.backup.spool import BackupSpool
from holland.core.backup.job import BackupJob

LOG = logging.getLogger(__name__)

class BackupManager(object):
    """Manage the backup process

    >>> mgr = BackupManager('/var/spool/holland')
    >>> mgr.backup('/etc/holland/backupsets/foo.conf', dry_run=True)
    """
    def __init__(self, spool_directory):
        self.spool = BackupSpool(spool_directory)

    def backup(self, config, dry_run=False):
        """Run a backup given a backupset name"""
        LOG.info("Backup: %s", config.name)
        config = validate_backup_config(config)
        name = config.name
        plugin = load_backup_plugin(config)
        LOG.info("+ Found plugin %s", plugin.name)
        store = self.spool.add_store(name)
        LOG.info("+ Initialized backup directory %s", store.path)
        job = BackupJob(plugin, config, store)
        job.run(dry_run)
        return job


    def cleanup(self, path):
        """Run a plugin's cleanup method"""
        from holland.core.config import load_config
        store = self.spool.load(path)
        config = load_config(os.path.join(store.path, 'backup.conf'))
        plugincls = load_backup_plugin(config)
        plugin = plugincls(store)
        plugin.configure(config)
        plugin.cleanup()
