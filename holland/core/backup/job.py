"""Run a backup job"""

import logging
from holland.core.plugin import load_plugin
from holland.core.config import Configspec
from holland.core.backup.util import Beacon
from holland.core.backup.hooks import *

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
        beacon = Beacon(['before-backup', 'after-backup', 'backup-failure'])
        if not dry_run:
            if self.config['holland:backup']['hooks']:
                setup_user_hooks(beacon, self.config)
            setup_builtin_hooks(beacon, self.config)
        else:
            setup_dryrun_hooks(beacon, self.config)

        try:
            self.plugin.configure(self.config)
            LOG.info("+ Configured plugin")
            self.plugin.setup(self.store)
            LOG.debug("+ Ran plugin setup")
            self.plugin.pre()
            LOG.info("+ Ran plugin pre")
            # allow before-backup hooks to abort immediately
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
            beacon.notify('backup-failure', job=self)
            raise
        beacon.notify('after-backup', job=self)

    #@staticmethod
    def configspec():
        from textwrap import dedent
        return Configspec.parse(dedent("""
        [holland:backup]
        plugin                  = string
        auto-purge-failures     = boolean(default=yes)
        purge-policy            = option("manual",
                                         "before-backup",
                                         "after-backup",
                                         default="after-backup")
        backups-to-keep         = integer(default=1)
        estimated-size-factor   = float(default=1.0)
        hooks                   = boolean(default="yes")
        before-backup           = force_list(default=list())
        after-backup            = force_list(default=list())
        backup-failure          = force_list(default=list())
        """).splitlines())
    configspec = staticmethod(configspec)
