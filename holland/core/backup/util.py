"""utility functions"""

from holland.core.config import load_config
from holland.core.plugin import load_plugin
from holland.core.backup.error import BackupError
from holland.core.backup.spool import SpoolError
from holland.core.util.fmt import format_bytes

def load_backup_config(name, config_dir=None):
    """Load a backup configuration given a name/path"""
    if not name.endswith('.conf'):
        name += '.conf'
    if config_dir and not os.path.isabspath(name):
        name = os.path.join(config_dir, 'backupsets', name)

    cfg = load_config(name)
    cfg.validate_config("""
    [holland:backup]
    auto-purge-failures = boolean(default=yes)
    purge-policy = option(manual,before-backup,after-backup, default=after-backup)
    backups-to-keep = integer(default=1)
    estimated-size-factor = float(default=1.0)
    """.splitlines())
    return cfg

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    return load_plugin('holland.backup', name)

class DryRunWrapper(object):
    """Wrap a plugin and always call its dry_run method
    rather than backup()
    """
    plugin = None

    def __init__(self, plugin):
        self.plugin = plugin

    def backup(self):
        self.dry_run()

    def __getattribute__(self, key):
        return getattr(self.plugin, key)

class SafeSignal(object):
    """Wrap a signal and do nothing with its send/send_robust methods"""

    def __init__(self, signal):
        self.signal = signal

    def send(self, *args, **kwargs):
        pass

    def send_robust(self, *args, **kwargs):
        pass


class FailureAutoPurger(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, sender, signal, job, **kwargs):
        job.store.purge()
        self.logger.info("Purged failed backup %s", job.store.path)


class BackupRotater(object):
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Initialized BackupRotater")

    def __call__(self, sender, signal, job, **kwargs):
        self.logger.info("Rotating backups")
        retention_count = job.config['holland:backup']['backups-to-keep']
        backups = job.store.oldest(n=retention_count)
        for backup in backups:
            backup.purge()
            self.logger.info("Purged %s", backup.path)


class BackupSpaceChecker(object):

    def __init__(self, logger):
        self.logger = logger

    def __call__(self, sender, signal, job, **kwargs):
        try:
            bytes = job.plugin.estimate()
        except (KeyboardInterrupt, SystemExit, BackupError):
            raise
        except:
            raise BackupError("Space estimate failed", sys.exc_info()[1])

        self.logger.info("%s plugin estimated backup size to be %s",
                job.plugin.name, format_bytes(bytes))
        bytes *= job.config['holland:backup']['estimated-size-factor']
        self.logger.info("Scaled estimated by %.2f%% to %s",
                         job.config['holland:backup']['estimated-size-factor'],
                         format_bytes(bytes))
        self.logger.info("Estimated %d bytes", bytes)
        try:
            job.store.check_space(bytes)
        except SpoolError:
            raise BackupError("Insufficient space on %s. "
                              "Required %s but only %s available" % 
                              (job.store.path, format_bytes(bytes),
                                  format_bytes(job.store.spool_capacity())))
