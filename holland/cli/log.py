"""Log utility functions"""

import os, sys
import warnings
import logging

DEFAULT_LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

LOG = logging.getLogger(__name__)

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

def log_warning(message, category, filename, lineno, _file=None, _line=None):
    """Log a warning message.

    This currently only logs DeprecationWarnings at debug level and otherwise
    only logs the message at 'info' level.  The formatted warning can be
    seen by enabling debug level logging.
    """
    log = logging.getLogger()
    args = [x for x in (_line,)]
    warning_string = warnings.formatwarning(message,
                                            category,
                                            filename,
                                            lineno, *args)
    if category == DeprecationWarning:
        log.debug("(%s) %s", _file, warning_string)
    else:
        log.debug(warning_string)
        log.warn("%s", message)

def configure_warnings():
    """Ensure warnings go through log_warning"""
    # Monkey patch in routing warnings through logging
    warnings.showwarning = log_warning


def configure_logging(config):
    """Configure CLI logging based on config

    config must be a dict-like object that has 3 paramters:
    * level - the log level
    * format - the log output format
    * filename - what file to log to (if any)
    """
    _clear_root_handlers()

    if os.isatty(sys.stderr.fileno()):
        configure_logger(logger=logging.getLogger(),
                         handler=logging.StreamHandler(),
                         fmt='%(message)s',
                         level=config['level'])

    try:
        configure_logger(logger=logging.getLogger(),
                         handler=logging.FileHandler(config['filename']),
                         fmt=config['format'],
                         level=config['level'])
    except IOError, exc:
        LOG.info("Failed to open log file: %s", exc)
        LOG.info("Skipping file logging.")

    configure_warnings()
