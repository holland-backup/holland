from base import *
from manager import *
from error import *

default_pluginmgr = EntrypointPluginManager()

iterate_plugins = default_pluginmgr.iterate
load_plugin = default_pluginmgr.load
