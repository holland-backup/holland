"""Standard Holland Backup API classes"""

import logging
from holland.core.plugin import load_plugin, ConfigurablePlugin
from holland.core.backup.spool import SpoolError
from holland.core.backup.error import BackupError
from holland.core.backup.hooks import *
from holland.core.dispatch import Signal

LOG = logging.getLogger(__name__)

class BackupJob(object):
    """A backup job that may be created and passed to a backup manager in order
    to perform a backup"""

    def __init__(self, plugin, config, store):
        self.plugin = plugin
        self.config = config
        self.store = store

    def init_hooks(self, events):
        """Initialize hooks based on the job config"""
        config = self.config['holland:backup']
        LOG.info("+++ Initializing hooks")
        for event, signal in events.items():
            for name in config[event]:
                if name in ('space-check', 'auto-purge', 'rotate-backups'):
                    continue
                hook = load_plugin('holland.hooks', name)(name)
                hook.configure(self.config)
                LOG.info("Connecting %r(%s) to %r(%s)", signal, event, hook,
                        name)
                signal.connect(hook, sender=None)
        events['pre-backup'].connect(CheckForSpaceHook('space-check'))
        events['pre-backup'].connect(WriteConfigHook('write-config'))
        if config['auto-purge-failures']:
            events['fail-backup'].connect(AutoPurgeFailuresHook('auto-purge'))
        if config['purge-policy'] == 'after-backup':
            events['post-backup'].connect(RotateBackupsHook('rotate-backups'))
        elif config['purge-policy'] == 'before-backup':
            events['post-backup'].connect(RotateBackupsHook('rotate-backups'))

    def notify(self, signal, robust=True):
        if robust:
            results = signal.send_robust(sender=None, job=self)
            for signal, result in results:
                if isinstance(result, Exception):
                    raise result
        else:
            signal.send(sender=None, job=self)

    def run(self, dry_run=False):
        """Run through a backup lifecycle"""
        backup_pre = Signal(providing_args=['job'])
        backup_post = Signal(providing_args=['job'])
        backup_fail = Signal(providing_args=['job'])
        if not dry_run:
            self.init_hooks({
                'pre-backup'    : backup_pre,
                'post-backup'   : backup_post,
                'fail-backup'   : backup_fail,
            })
        else:
            hook = DryRunPurgeHook('dry-run-purge')
            backup_post.connect(hook, sender=None)
            backup_fail.connect(hook, sender=None)

        try:
            self.plugin.configure(self.config)
            LOG.info("+ Configured plugin")
            self.plugin.setup(self.store)
            LOG.debug("+ Ran plugin setup")
            self.plugin.pre()
            LOG.info("+ Ran plugin pre")
            self.notify(backup_pre, robust=False) # abort immediately
            try:
                LOG.info("Running backup")
                if dry_run:
                    self.plugin.dry_run()
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
            self.notify(backup_fail)
            raise
        self.notify(backup_post)

class BackupPlugin(ConfigurablePlugin):
    """Interface that Holland Backup Plugins should conform to"""

    def backup(self, path):
        """Backup to the specified path"""
        raise NotImplementedError()

    def dry_run(self, path):
        """Perform a dry-run backup to the specified path"""
        raise NotImplementedError()

    def backup_info(self):
        """Provide information about this backup"""
        raise NotImplementedError()

