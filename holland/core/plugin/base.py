"""Base plugin classes"""

class PluginInfo(object):
    """Information about a plugin

    An instance of this class should be returned
    by a Plugin object's plugin_info() method
    """
    #@property
    def name(self):
        """Canonical name of this plugin"""
        raise NotImplementedError()
    name = property(name)

    #@property
    def summary(self):
        """One-line summary of this plugin"""
        raise NotImplementedError()
    summary = property(summary)

    #@property
    def description(self):
        """Text blob description of this plugin"""
        raise NotImplementedError()
    description = property(description)

    #@property
    def author(self):
        """Author of this plugin"""
        raise NotImplementedError()
    author = property(author)

    #@property
    def version(self):
        """Version string for this plugin"""
        raise NotImplementedError()
    version = property(version)


class BasePlugin(object):
    """Base class from which all Holland plugins should derive"""
    def setup(self):
        """Called by a manager to allow this plugin to perform any necessary
        setup"""
        raise NotImplementedError()

    def teardown(self):
        """Called by a manager when it is done with this plugin"""
        raise NotImplementedError()

    def plugin_info(self):
        """Provide information about this plugin"""
        raise NotImplementedError()

class ConfigurablePlugin(BasePlugin):
    """A plugin that accepts a configuration dictionary"""

    def configspec(self):
        """Provide a configspec that this plugin expects"""
        raise NotImplementedError()

    def configure(self, config):
        """Configure this plugin with the given dict-like object"""
        raise NotImplementedError()
