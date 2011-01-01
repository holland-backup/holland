"""Base plugin classes"""

class PluginInfo(object):
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
        raise NotImplementedError()
    author = property(author)

    #@property
    def version(self):
        """Version string for this plugin"""
        raise NotImplementedError()
    version = property(version)


class BasePlugin(object):
    def plugin_info(self):
        return PluginInfo()

class ConfigurablePlugin(object):
    def configspec(self):
        raise NotImplementedError()

    def configure(self, config):
        raise NotImplementedError()
