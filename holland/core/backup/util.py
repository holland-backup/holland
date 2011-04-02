"""
    holland.core.backup.util
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utility methods used by holland.core.backup

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import logging
from holland.core.plugin import load_plugin, PluginError
from holland.core.backup.plugin import BackupPlugin
from holland.core.backup.error import BackupError

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
    configspec.merge(plugin.configspec())
    for hook in config['holland:backup']['hooks']:
        try:
            name = config[hook]['plugin']
        except KeyError:
            LOG.error("No section [%s] defined for hook %s", hook, hook)
            continue
        plugin = load_plugin('holland.hooks', name)
        section = configspec.setdefault(hook, configspec.__class__())
        section['plugin'] = 'string'
        section.merge(plugin.configspec())
    configspec.validate(config)

