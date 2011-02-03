"Standard exceptions raised by the holland.core.plugin API"

class PluginError(Exception):
    """Base plugin error exception"""

class PluginLoadError(PluginError):
    """Failure to load a plugin

    :attr group: plugin group
    :attr name:  plugin name
    :attr exc:   original exception raised
    """
    def __init__(self, group, name, exc):
        super(PluginLoadError, self).__init__(group, name, exc)
        self.group = group
        self.name = name
        self.exc = exc

class PluginNotFoundError(PluginError):
    """Raise when a plugin could not be found"""
    def __init__(self, group, name):
        super(PluginNotFoundError, self).__init__(group, name)
        self.group = group
        self.name = name

    def __str__(self):
        return "No plugin %s in group %s" % (self.name, self.group)
