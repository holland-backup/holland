"""utility functions"""

import logging
from holland.core.plugin import load_plugin, PluginError
from holland.core.dispatch import Signal
from holland.core.backup.base import BackupError, BackupPlugin

LOG = logging.getLogger(__name__)

def load_backup_plugin(config):
    """Load a backup plugin from a backup config"""
    name = config['holland:backup']['plugin']
    if not name:
        raise BackupError("No plugin specified in [holland:backup] in %s" %
                          config.path)
    try:
        return load_plugin('holland.backup', name)
    except PluginError, exc:
        raise BackupError(str(exc), exc)

def validate_config(config):
    """Validate a config file

    This method collects the configspecs from all the plugins involved in a
    config and merges them together and validates a config in one pass.

    :raises: ValidateError on validation errors
    """
    configspec = BackupPlugin.configspec()
    configspec.validate(config, ignore_unknown_sections=True)
    backup_plugin = config['holland:backup']['plugin']
    plugin = load_plugin('holland.backup', backup_plugin)
    print "Including backup plugin '%s' configspec" % backup_plugin
    configspec.merge(plugin.configspec())
    for hook in config['holland:backup']['hooks']:
        try:
            name = config[hook]['plugin']
        except KeyError:
            LOG.error("No section [%s] defined for hook %s", hook, hook)
            continue
        plugin = load_plugin('holland.hooks', name)
        print "Including hook '%s' configspec" % hook
        section = configspec.setdefault(hook, configspec.__class__())
        section['plugin'] = 'string'
        section.merge(plugin.configspec())
    configspec.validate(config)

class Beacon(dict):
    """Simple Signal container"""
    def __init__(self, names):
        dict.__init__(self)
        for name in names:
            self[name] = Signal()

    def notify(self, name, robust=True, **kwargs):
        """Send notifications to the named signal in this SignalGroup

        If ``robust`` is True then use send_robust and raise an exception
        at the end if necessary.

        ``**kwargs`` wil be send to each registered receiver for the signal
        """
        signal = self[name]
        if robust:
            for receiver, result in signal.send_robust(sender=None, **kwargs):
                if isinstance(result, Exception):
                    LOG.debug("Received (%r) raised an exception: %r",
                            receiver, result)
                    raise result
        else:
            signal.send(sender=None, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key.replace('_', '-')]
        except KeyError:
            raise AttributeError('%r object has no attribute %r' %
                                 (self.__class__.__name__, key))
