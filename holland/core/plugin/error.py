class PluginError(Exception):
    """Base plugin error exception"""

class PluginImportError(PluginError):
    """Raised when importing a plugin fails

    :attr module: module this plugin belongs to
    """

    def __init__(self, module):
        self.module = module

class PluginInstanceError(PluginError):
    """Raise when attempting to instantiate a plugin class"""

    def __init__(self, cls):
        self.cls = cls

class PluginNotFoundError(PluginError):
    """Raise when a plugin could not be found"""
