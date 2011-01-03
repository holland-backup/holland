"""holland.core plugin API"""

from holland.core.plugin.base import *
from holland.core.plugin.manager import *
from holland.core.plugin.error import *

default_pluginmgr = EntrypointPluginManager()

iterate_plugins = default_pluginmgr.iterate
load_plugin = default_pluginmgr.load
