"""utility functions"""

from holland.core.config import load_config, std_backup_spec
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
    cfg.validate_config(std_backup_spec)
    return cfg

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    return load_plugin('holland.backup', name)

