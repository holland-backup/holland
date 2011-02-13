"""Log utility functions"""

import os, sys
import logging

DEFAULT_LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

def _clear_root_handlers():
    """Remove all pre-existing handlers on the root logger"""
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)

def configure_basic_logger():
    """Configure a simple console logger"""
    root = logging.getLogger()

    if os.isatty(sys.stderr.fileno()):
        class NullHandler(logging.Handler):
            """No-op log handler"""
            def emit(self, something):
                """Null emitter"""
                pass
        handler = NullHandler()
    else:
        handler = logging.StreamHandler()

    configure_logger(logger=root,
                     handler=handler,
                     fmt=DEFAULT_LOG_FORMAT,
                     level=logging.INFO)

def configure_logger(logger, handler, fmt, level):
    """Configure a new logger"""
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)

def configure_logging(config):
    _clear_root_handlers()

    if os.isatty(sys.stderr.fileno()):
        configure_logger(logger=logging.getLogger(),
                         handler=logging.StreamHandler(),
                         fmt='%(message)s',
                         level=config['level'])

    try:
        configure_logger(logger=logging.getLogger(),
                         handler=logging.FileHandler(config['file']),
                         fmt=config['format'],
                         level=config['level'])
    except IOError, exc:
        logging.info("Failed to open log file: %s", exc)
        logging.info("Skipping file logging.")
