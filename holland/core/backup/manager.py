"""primary backup api

>>> mgr = BackupManager('/var/spool/holland')
>>> mgr.backup('/etc/holland/backupsets/foo.conf', dry_run=True)
"""

import os, sys
import logging
from holland.core.backup.util import load_backup_config, load_backup_plugin, \
                                     DryRunWrapper, SafeSignal
from holland.core.backup.spool import BackupSpool
from holland.core.backup.base import BackupJob
from holland.core.dispatch import Signal

LOG = logging.getLogger(__name__)

class BackupManager(object):
    """Manage the backup process

    >>> mgr = BackupManager('/var/spool/holland')
    >>> mgr.backup('/etc/holland/backupsets/foo.conf', dry_run=True)
    """
    def __init__(self, spool_directory, config_dir):
        self.spool = BackupSpool(spool_directory)
        self.config_dir = config_dir
        self.backup_pre  = Signal()
        self.backup_post = Signal()
        self.backup_fail = Signal()

    def backup(self, name, dry_run=False):
        """Run a backup given a backupset name"""
        LOG.info("Backup: %s", name)
        config = load_backup_config(name, config_dir=self.config_dir)
        LOG.info("+ Loaded config %s", config.filename)
        name = os.path.splitext(os.path.basename(name))[0]
        plugincls = load_backup_plugin(config)
        LOG.info("+ Found plugin %s", plugincls.name)
        store = self.spool.add_store(name)
        LOG.info("+ Initialized backup directory %s", store.path)

        try:
            plugin = plugincls(store)
            LOG.info("+ Initialized plugin")
        except:
            store.purge()
            raise
        job = BackupJob(plugin, config, store)
        if dry_run:
            self._dry_run(job)
        else:
            self._run(job)

    def _run(self, job):
        """Run through a backup lifecycle"""
        plugin = job.plugin
        store = job.store

        try:
            self.backup_pre.send_robust(job)
            plugin.configure(job.config)
            LOG.info("+ Configured plugin")
            plugin.setup()
            LOG.debug("+ Ran plugin setup")
            try:
                store.check_space(plugin.estimate())
                LOG.info("+ Verified free space is available")
                LOG.info("Running backup")
                plugin.backup()
            finally:
                try:
                    plugin.teardown()
                    LOG.debug("+ Ran plugin cleanup")
                except:
                    LOG.warning("+ Error while running plugin shutdown.")
                    LOG.warning("  Please see the trace log")
        except:
            self.backup_fail.send_robust(job)
            raise
        self.backup_post.send_robust(job)

    def _dry_run(self, job):
        """Dry-Run through a plugin lifecycle

        Unlike a normal backup, this temporarily disables all hooks
        and calls dry_run() rather than backup() on the plugin
        """
        # safe plugin will call dry_run rather than backup on the plugin
        job.plugin = DryRunWrapper(job.plugin)
        # All hooks are skipped
        self.backup_pre = SafeSignal(self.backup_pre)
        self.backup_post = SafeSignal(self.backup_post)
        self.backup_fail = SafeSignal(self.backup_post)
        try:
            self._run(job)
        finally:
            # always purge the store on dry-run
            try:
                job.store.purge()
            except:
                LOG.warn("Failed to purge dry-run backup directory: %s",
                         sys.exc_info()[1])
            # restore signals
            self.backup_pre = self.backup_pre.signal
            self.backup_post = self.backup_post.signal
            self.backup_fail = self.backup_fail.signal

    def cleanup(self, path):
        """Run a plugin's cleanup method"""
        from holland.core.config import load_config
        store = self.spool.load(path)
        config = load_config(os.path.join(store.path, 'backup.conf'))
        plugincls = load_backup_plugin(config)
        plugin = plugincls(store)
        plugin.configure(config)
        plugin.cleanup()
