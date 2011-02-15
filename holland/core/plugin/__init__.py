"""holland.core plugin API"""

from holland.core.plugin.base import BasePlugin, ConfigurablePlugin
from holland.core.plugin.manager import EntrypointPluginManager
from holland.core.plugin.error import PluginError

default_pluginmgr = EntrypointPluginManager()

# Convenience methods
iterate_plugins = default_pluginmgr.iterate
load_plugin = default_pluginmgr.load
