"""utility functions"""

from holland.core.config import Config, Configspec
from holland.core.plugin import load_plugin
from holland.core.backup.error import BackupError
from holland.core.backup.spool import SpoolError
from holland.core.util.fmt import format_bytes

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
fail-backup             = force_list(default=list())
pre-backup              = force_list(default=list())
post-backup             = force_list(default=list())
""".splitlines())

def load_backup_config(name, config_dir=None):
    """Load a backup configuration given a name/path"""
    if not name.endswith('.conf'):
        name += '.conf'
    if config_dir and not os.path.isabspath(name):
        name = os.path.join(config_dir, 'backupsets', name)

    cfg = Config.read([name])
    std_backup_spec.validate(cfg)
    return cfg

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    return load_plugin('holland.backup', name)

