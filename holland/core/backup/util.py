"""utility functions"""

from holland.core.config import load_config
from holland.core.plugin import load_plugin

def load_backup_config(name, config_dir=None):
    """Load a backup configuration given a name/path"""
    if not name.endswith('.conf'):
        name += '.conf'
    if config_dir and not os.path.isabspath(name):
        name = os.path.join(config_dir, 'backupsets', name)
    return load_config(name)

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
