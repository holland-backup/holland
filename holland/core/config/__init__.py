"""
Module to read configuration files
"""

from .config import HOLLANDCFG, setup_config, load_backupset_config, \
                   BaseConfig, ConfigError
from .configobj import ConfigObj, ParseError, ConfigObjError

__all__ = [
    'HOLLANDCFG',
    'setup_config',
    'load_backupset_config',
    'BaseConfig'
]
