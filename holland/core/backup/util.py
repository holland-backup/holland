"""utility functions"""

from holland.core.config import Configspec
from holland.core.plugin import load_plugin
from holland.core.dispatch import Signal
from holland.core.backup.base import BackupError

std_backup_spec = Configspec.parse("""
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
""".splitlines())

def validate_backup_config(cfg):
    """Validate a backup configuration"""
    return std_backup_spec.validate(cfg)

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    if not name:
        raise BackupError("No plugin specified in [holland:backup] in %s" %
                          config.path)
    return load_plugin('holland.backup', name)

class Beacon(dict):
    """Simple Signal container"""
    def __init__(self, names):
        for name in names:
            self[name] = Signal()

    def notify(self, name, robust=True, **kwargs):
        signal = self[name]
        if robust:
            for receiver, result in signal.send_robust(sender=None, **kwargs):
                if isinstance(result, Exception):
                    raise result
        else:
            signal.send(sender=None, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key.replace('_', '-')]
        except KeyError:
            raise AttributeError('%r object has no attribute %r' %
                                 (self.__class__.__name__, key))
