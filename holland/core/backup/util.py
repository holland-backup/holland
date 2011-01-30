"""utility functions"""

import logging
from holland.core.plugin import load_plugin, PluginError
from holland.core.dispatch import Signal
from holland.core.backup.base import BackupError

LOG = logging.getLogger(__name__)

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    if not name:
        raise BackupError("No plugin specified in [holland:backup] in %s" %
                          config.path)
    try:
        plugincls = load_plugin('holland.backup', name)
    except PluginError, exc:
        raise BackupError(str(exc), exc)

    try:
        return plugincls(name)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception, exc:
        LOG.debug("Error when instantiating plugin class '%s': %s",
                  plugincls, exc, exc_info=True)
        raise BackupError("Failed to load plugin: %s" % name, exc)

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
