"""Holland core API"""

from holland.core.plugin import load_plugin, iterate_plugins
from holland.core.plugin import BasePlugin, PluginError
from holland.core.config import Config, ConfigError, Configspec
from holland.core.hooks import BaseHook
from holland.core.stream import open_stream
# spool management
from holland.core.backup import BackupSpool, BackupStore
# backup plugin base classes
from holland.core.backup import BackupPlugin, BackupError
# backup plugin api gateway
from holland.core.backup import BackupManager

__all__ = [
    'BasePlugin',
    'load_plugin',
    'iterate_plugins',
    'PluginError',
    'Config',
    'ConfigError',
    'Configspec',
    'BaseHook',
    'open_stream',
    'BackupSpool',
    'BackupStore',
    'BackupManager',
    'BackupPlugin',
    'BackupError',
]
