"""
    holland.core.plugin.base
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Base plugin classes for Holland

    :copyright: 2008-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from holland.core.config import Configspec

class BasePlugin(object):
    """The base Plugin class that all Holland plugins
    derive from.

    Plugins are always instantiated with a name of the
    plugin they were registered under. This will be a
    name like 'mysqldump' or 'mysql-lvm'.

    Plugins should override the plugin_info() method
    and provide a dict with the following attributes:
        * name          - canonical name of this plugin
        * author        - plugin author's name
        * summary       - one-line (<80 char) short description of this plugin
        * description   - multi-line text blurb describing this plugin
        * version       - the version of this plugin (e.g. '0.1a1')
        * api_version   - the version of the holland api this plugin is
                          designed to work with (e.g. '1.1')
    """
    #: name of this plugin
    name = None

    #: aliases for this plugin
    aliases = ()

    def __init__(self, name):
        self.name = name

    def plugin_info(self):
        """Provide information about this plugin

        :returns: dict of plugin metadata attributes
        """
        return dict(
            name='base-plugin',
            author='Holland',
            summary='<no summary>',
            description='<no description>',
            version='0.0',
            api_version='1.1'
        )

class ConfigurablePlugin(BasePlugin):
    """Base plugin class used by plugins that accept a config

    ConfigurablePlugins should provide two methods:
        * ``configspec()`` - Returns an instance of
          ``holland.core.config.Configspec`` describing the config that
          this plugin accepts
        * ``configure(config)`` - called by holland to configure this
          plugin with a config

    All configs are a subclass of ``holland.core.config.Config`` and behave as
    normal python dicts with additional methods documented in the config
    subpackage
    """
    config = None

    def configspec(self):
        """Provide a configspec that this plugin expects

        :returns: instance of holland.core.config.Configspec
        """
        return Configspec()

    def configure(self, config):
        """Configure this plugin with the given dict-like object

        The default behavior just sets the ``config`` attribute on
        this plugin instance.
        """
        self.config = config
