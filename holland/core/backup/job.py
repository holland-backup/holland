"""Run a backup job"""

import logging
from holland.core.backup.util import Beacon
from holland.core.backup.hooks import setup_user_hooks, setup_builtin_hooks, \
                                      setup_dryrun_hooks

LOG = logging.getLogger(__name__)

class BackupJob(object):
    """A backup job that may be created and passed to a backup manager in order
    to perform a backup"""

    def __init__(self, plugin, config, store):
        self.plugin = plugin
        self.config = config
        self.store = store

    def run(self, dry_run=False):
        """Run through a backup lifecycle"""
        beacon = Beacon(['setup-backup', 'before-backup',
                         'after-backup', 'backup-failure'])
        if not dry_run:
            if self.hooks():
                setup_user_hooks(beacon, self.config)
            setup_builtin_hooks(beacon, self.config)
        else:
            setup_dryrun_hooks(beacon)

        try:
            LOG.info("+ Running setup-backup hooks")
            beacon.notify('setup-backup', job=self, robust=False)
            control = self.config.pop('holland:backup')
            self.plugin.configure(self.config)
            self.config.insert(0, 'holland:backup', control)
            LOG.info("+ Configured plugin")
            self.plugin.setup(self.store)
            LOG.debug("+ Ran plugin setup")
            self.plugin.pre()
            LOG.info("+ Ran plugin pre")
            # allow before-backup hooks to abort immediately
            LOG.info("+ Running before-backup hooks")
            beacon.notify('before-backup', job=self, robust=False)
            try:
                LOG.info("Running backup")
                if dry_run:
                    self.plugin.dryrun()
                else:
                    self.plugin.backup()
            finally:
                try:
                    self.plugin.post()
                    LOG.debug("+ Ran plugin post")
                except:
                    LOG.warning("+ Error while running plugin shutdown.")
                    LOG.warning("  Please see the trace log")
        except:
            LOG.info("+ Running backup failure hooks")
            beacon.notify('backup-failure', job=self)
            raise
        LOG.info("+ Running after-backup hooks")
        beacon.notify('after-backup', job=self)

    def hooks(self):
        """Extract hooks from the global config"""
        return self.global_config()['hooks']

    def global_config(self):
        """Extract the [holland:backup] section from the job config"""
        return self.config['holland:backup']
