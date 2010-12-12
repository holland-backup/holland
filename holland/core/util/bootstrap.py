"""
Functions to support bootstrapping.

These functions should only be called when starting up a holland session.
They initialize things like logging and the config system.
"""
import os
import sys
import logging
import warnings
from holland.core.plugin import add_plugin_dir
from holland.core.config import hollandcfg, setup_config as _setup_config
from holland.core.log import setup_console_logging, setup_file_logging, clear_root_handlers
from holland.core.spool import spool

LOGGER = logging.getLogger(__name__)

def setup_config(opts):
    if not opts.quiet:
        debug = opts.log_level == 'debug'
        setup_console_logging(level=[logging.INFO,logging.DEBUG][debug])
    try:
        _setup_config(opts.config_file)
    except IOError, e:
        LOGGER.error("Failed to load holland config: %s", e)
        sys.exit(os.EX_CONFIG)

def log_warnings(message, category, filename, lineno, file=None, line=None):
    WARNLOG = logging.getLogger("Python")
    logging.debug("message=%s message=%r category=%r", message, message, category)
    warning_string = warnings.formatwarning(message,
                                            category,
                                            filename,
                                            lineno)
    if category == DeprecationWarning:
        WARNLOG.debug("%s", warning_string)
    else:
        WARNLOG.debug(warning_string)
        WARNLOG.warn("%s", message)

def setup_logging(opts):
    clear_root_handlers()
    if hasattr(opts, 'log_level'):
        log_level = opts.log_level or hollandcfg.lookup('logging.level')
    else:
        log_level = hollandcfg.lookup('logging.level')

    if (os.isatty(sys.stdin.fileno()) and not opts.quiet):
        setup_console_logging(level=log_level)

    if hollandcfg.lookup('logging.filename'):
        setup_file_logging(filename=hollandcfg.lookup('logging.filename'),
                           level=log_level)

    # Monkey patch in routing warnings through logging
    old_showwarning = warnings.showwarning
    warnings.showwarning = log_warnings

def setup_umask():
    os.umask(hollandcfg.lookup('holland.umask'))

def setup_path():
    if hollandcfg.lookup('holland.path'):
        os.putenv('PATH', hollandcfg.lookup('holland.path'))
        os.environ['PATH'] = hollandcfg.lookup('holland.path')

def setup_plugins():
    map(add_plugin_dir, hollandcfg.lookup('holland.plugin-dirs'))

def bootstrap(opts):
    # Setup the configuration
    setup_config(opts)
    # Setup logging per config
    setup_logging(opts)
    # use umask setting
    setup_umask()
    # setup tmpdir
    if hollandcfg.lookup('holland.tmpdir'):
        os.environ['TMPDIR'] = str(hollandcfg.lookup('holland.tmpdir'))
    # configure our PATH
    setup_path()
    # Setup plugin directories
    setup_plugins()
    # Setup spool
    spool.path = hollandcfg.lookup('holland.backup-directory')
