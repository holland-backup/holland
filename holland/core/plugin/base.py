"""Base plugin classes"""

class PluginInfo(object):
    """Information about a plugin

    An instance of this class should be returned
    by a Plugin object's plugin_info() method
    """
    #: Canonical name of the plugin
    name = ''
    #: One-line summary of this plugin's functionality
    summary = ''
    #: Textual description of this plugin
    description = ''
    #: Name(s) of the author of this plugin
    author = ''

    # XXX: Versions should be standardized - perhaps per distutils2.version
    # semantics
    #: Version for this plugin
    version = (0, 0, 0)
    #: Version of holland this plugin was intended for
    holland_version = (0, 0, 0)

    def __init__(self,
                 name,
                 summary,
                 description,
                 author,
                 version,
                 holland_version):
        self.name = name
        self.summary = summary
        self.description = description
        self.author = author
        self.version = version
        self.holland_version = holland_version


class BasePlugin(object):
    """Base class from which all Holland plugins should derive"""
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
