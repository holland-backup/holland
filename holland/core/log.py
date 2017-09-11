import os
import sys
import logging

__all__ = [
    'clear_root_handlers',
    'setup_console_logging',
    'setup_file_logging'
]

DEFAULT_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S'
DEFAULT_LOG_FORMAT = '%(asctime)s PID-%(process)s [%(levelname)s] %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

class NullHandler(logging.Handler):
    def emit(self, record):
            pass

def clear_root_handlers():
    root = logging.getLogger()
    map(root.removeHandler, root.handlers)

def setup_console_logging(level=DEFAULT_LOG_LEVEL, 
                          format='%(message)s', 
                          datefmt=DEFAULT_DATE_FORMAT):
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(format, datefmt)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def setup_file_logging(filename, 
                       level=DEFAULT_LOG_LEVEL, 
                       format=DEFAULT_LOG_FORMAT, 
                       datefmt=DEFAULT_DATE_FORMAT):
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.FileHandler(filename, 'a', encoding='utf8')
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
