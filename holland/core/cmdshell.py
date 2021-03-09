"""This file defines the default options available
 and the entry point for holland command"""

import logging
import os
import sys

from pkg_resources import get_distribution

from holland.core.command import parse_sys, print_help, run
from holland.core.config.checks import is_logging_level
from holland.core.util.bootstrap import bootstrap

LOG = logging.getLogger(__name__)
HOLLAND_VERSION = get_distribution("holland").version

# main entrypoint for holland's cmdshell 'hl'
def main():
    """The main entrypoint for holland's cmdshell"""

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    opts, args = parse_sys(sys.argv[1:])

    if args:
        args = args[0].split(",")
    logging.raiseExceptions = bool(opts.log_level == "debug")
    if "log_level" in opts:
        opts.log_level = is_logging_level(opts.log_level)

    if opts.command is None:
        print_help()
        sys.exit(1)

    # Bootstrap the environment
    bootstrap(opts)

    LOG.info("Holland %s started with pid %d", HOLLAND_VERSION, os.getpid())
    return run(opts, args)
