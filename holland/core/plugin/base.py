"""Base plugin classes"""

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

    def setup(self):
        """Called by a manager to allow this plugin to perform any necessary
        setup"""

    def teardown(self):
        """Called by a manager when it is done with this plugin"""

    def plugin_info(self):
        """Provide information about this plugin

        :returns: Instance of ``PluginInfo``
        """
        raise NotImplementedError()

class ConfigurablePlugin(BasePlugin):
    """A plugin that accepts a configuration dictionary"""

    #XXX: Specify a standard configspec format
    #@classmethod
    def configspec(cls):
        """Provide a configspec that this plugin expects

        :returns: Any parseable data that ConfigObj accepts
        """
        raise NotImplementedError()
    configspec = classmethod(configspec)

    def configure(self, config):
        """Configure this plugin with the given dict-like object"""
