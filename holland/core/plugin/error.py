"""
    holland.core.plugin.error
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Standard exceptions raised by the Holland plugin API

    :copyright: 2008-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

class PluginError(Exception):
    """Base plugin error exception"""

class PluginLoadError(PluginError):
    """Failure to load a plugin

    Raised by a PluginManager when a plugin is found but an error is
    encountered when importing or instantiating a plugin class

    :attr group: plugin group
    :attr name:  plugin name
    :attr exc:   original exception raised
    """
    def __init__(self, group, name, exc):
        PluginError.__init__(self, group, name, exc)
        self.group = group
        self.name = name
        self.exc = exc

class PluginNotFoundError(PluginError):
    """Failure to find a plugin

    This error is raised by a PluginManager when a plugin could not
    be found for the given group and name combination.

    :attr group: plugin group
    :attr name:  plugin name
    """
    def __init__(self, group, name):
        PluginError.__init__(self, group, name)
        self.group = group
        self.name = name

    def __str__(self):
        return "No plugin %s in group %s" % (self.name, self.group)
