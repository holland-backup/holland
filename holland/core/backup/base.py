"""Standard Holland Backup API classes"""

from holland.core.plugin import load_plugin, ConfigurablePlugin
from holland.core.backup.spool import SpoolError
from holland.core.backup.error import BackupError
from holland.core.hooks import BaseHook

class BackupJob(object):
    """A backup job that may be created and passed to a backup manager in order
    to perform a backup"""

    def __init__(self, plugin, config, store):
        self.plugin = plugin
        self.config = config
        self.store = store
        self.init_hooks(events={
            'pre-backup'    : self.backup_pre,
            'post-backup'   : self.backup_post,
            'failed-backup' : self.backup_fail,
        })

    def init_hooks(self, events):
        """Initialize hooks based on the job config"""
        config = self.config['holland:backup']
        for event, signal in self.events.items():
            for name in config[event]:
                hook = load_plugin('holland.hooks', name)
                hook.configure(self.config)
                signal.connect(sender=self.store.name, hook)

    def notify(self, signal):
        signal.sender_robust(job=self)

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
            cleanup = lambda sender, signal, job: job.store.purge()
            backup_post.connect(sender=None, cleanup)
            backup_fail.connect(sender=None, cleanup)

        try:
            plugin.configure(self.config)
            LOG.info("+ Configured plugin")
            plugin.setup(self.store)
            LOG.debug("+ Ran plugin setup")
            plugin.pre()
            LOG.info("+ Ran plugin pre")
            self.notify(backup_pre)
            try:
                LOG.info("Running backup")
                if dry_run:
                    plugin.dry_run()
                else:
                    plugin.backup()
            finally:
                try:
                    plugin.post()
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


class BackupHook(BaseHook):
    def execute(self, job):
        """Process a backup job event"""
