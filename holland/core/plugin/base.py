"""Base plugin classes"""
from holland.core.config import Configspec

class PluginInfo(dict):
    """Information about a plugin

    An instance of this class should be returned
    by a Plugin object's plugin_info() method
    """

    def is_compatible(self, required_versoin):
        from version import NormalizedVersion as V
        try:
            return (V(self.api_version) == V(required_version))
        except AttributeError:
            return False

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError('%s object has no attribute %r' %
                                 (self.__class__.__name__, name))

class BasePlugin(object):
    """Base class from which all Holland plugins should derive"""
    #: name of this plugin
    name = None

    #: aliases for this plugin
    aliases = ()

    def __init__(self, name):
        self.name = name

    def plugin_info(self):
        """Provide information about this plugin

        :returns: Instance of ``PluginInfo``
        """
        raise NotImplementedError()

class ConfigurablePlugin(BasePlugin):
    """A plugin that accepts a configuration dictionary"""

    #py23compat
    #@classmethod
    def configspec(cls):
        """Provide a configspec that this plugin expects

        :returns: instance of holland.core.config.Configspec
        """
        return Configspec()
    configspec = classmethod(configspec)

    def configure(self, config):
        """Configure this plugin with the given dict-like object"""
        config.validate_config(self.configspec())
        self.config = config
