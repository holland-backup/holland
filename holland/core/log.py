"""Configure console and file logging
"""

import logging

__all__ = [
    'clear_root_handlers',
    'setup_console_logging',
    'setup_file_logging'
]

DEFAULT_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S'
DEFAULT_LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

class NullHandler(logging.Handler):
    """Send Log messages to Null"""
    def emit(self, record):
        pass

def clear_root_handlers():
    """Close file handles"""
    root = logging.getLogger()
    list(map(root.removeHandler, root.handlers))

def setup_console_logging(level=DEFAULT_LOG_LEVEL,
                          msg_format='%(message)s',
                          datefmt=DEFAULT_DATE_FORMAT):
    """Setup Logging to the Console"""
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(msg_format, datefmt)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def setup_file_logging(filename,
                       level=DEFAULT_LOG_LEVEL,
                       msg_format=DEFAULT_LOG_FORMAT):
    """Setup logging to file defined in /etc/holland/holland.conf"""
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.FileHandler(filename, 'a', encoding='utf8')
    formatter = logging.Formatter(msg_format)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
