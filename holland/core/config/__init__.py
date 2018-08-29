"""
Module to read configuration files
"""

try:
    from .configobj import ConfigObj, ParseError, ConfigObjError
except ImportError:
    from configobj import ConfigObj, ParseError, ConfigObjError

from .config import HOLLANDCFG, setup_config, load_backupset_config, \
                   BaseConfig, ConfigError


__all__ = [
    'HOLLANDCFG',
    'setup_config',
    'load_backupset_config',
    'BaseConfig'
]
