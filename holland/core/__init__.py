"""Holland core API"""

from holland.core.plugin import load_plugin, iterate_plugins, BasePlugin, PluginError
from holland.core.config import Config, Configspec
from holland.core.hooks import BaseHook
from holland.core.stream import open_stream
from holland.core.backup import *

__all__ = [
    'BasePlugin',
    'load_plugin',
    'iterate_plugins',
    'PluginError',
    'Config',
    'Configspec',
    'BaseHook',
    'open_stream',
    'BackupSpool',
    'BackupStore',
    'BackupManager',
    'BackupPlugin',
    'BackupError',
]
