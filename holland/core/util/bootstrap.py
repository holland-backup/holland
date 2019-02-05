"""
Functions to support bootstrapping.

These functions should only be called when starting up a holland session.
They initialize things like logging and the config system.
"""
import os
import sys
import logging
from holland.core.plugin import add_plugin_dir
from holland.core.config import HOLLANDCFG, setup_config as _setup_config
from holland.core.log import setup_console_logging, setup_file_logging, clear_root_handlers
from holland.core.spool import SPOOL

LOG = logging.getLogger(__name__)


def setup_config(opts):
    """
    Setup Config
    """
    if not opts.quiet:
        debug = opts.log_level == "debug"
        setup_console_logging(level=[logging.INFO, logging.DEBUG][debug])
    try:
        _setup_config(opts.config_file)
    except IOError as ex:
        LOG.error("Failed to load holland config: %s", ex)
        sys.exit(os.EX_CONFIG)


def setup_logging(opts):
    """
    Setup log file
    """
    clear_root_handlers()
    if hasattr(opts, "log_level"):
        log_level = opts.log_level or HOLLANDCFG.lookup("logging.level")
    else:
        log_level = HOLLANDCFG.lookup("logging.level")

    if not opts.quiet:
        setup_console_logging(level=log_level)

    if HOLLANDCFG.lookup("logging.filename"):
        try:
            if HOLLANDCFG.lookup("logging.format"):
                setup_file_logging(
                    filename=str(HOLLANDCFG.lookup("logging.filename")),
                    level=log_level,
                    msg_format=HOLLANDCFG.lookup(str("logging.format")),
                )
            else:
                setup_file_logging(
                    filename=str(HOLLANDCFG.lookup("logging.filename")), level=log_level
                )
        except IOError as exc:
            LOG.warning("Skipping file logging: %s", exc)


def setup_umask():
    """
    get file umask
    """
    os.umask(HOLLANDCFG.lookup("holland.umask"))


def setup_path():
    """
    Lookup config file path
    """
    if HOLLANDCFG.lookup("holland.path"):
        os.putenv("PATH", HOLLANDCFG.lookup("holland.path"))
        os.environ["PATH"] = HOLLANDCFG.lookup("holland.path")


def setup_plugins():
    """
    Setup plugins
    """
    for location in HOLLANDCFG.lookup("holland.plugin-dirs"):
        add_plugin_dir(location)


def bootstrap(opts):
    """
    Called by main() to setup everything
    """
    # Setup the configuration
    setup_config(opts)
    # use umask setting
    setup_umask()
    # Setup logging per config
    setup_logging(opts)
    # setup tmpdir
    if HOLLANDCFG.lookup("holland.tmpdir"):
        os.environ["TMPDIR"] = str(HOLLANDCFG.lookup("holland.tmpdir"))
    # configure our PATH
    setup_path()
    # Setup plugin directories
    setup_plugins()
    # Setup spool
    SPOOL.path = HOLLANDCFG.lookup("holland.backup-directory")
