"""
Setup functions to import commnad plugins
"""

import os
import sys
import logging
from holland.core.plugin import get_commands
from .command import Command, PARSER

__all__ = ["Command", "run", "PARSER"]

LOG = logging.getLogger(__name__)


def setup_commands():
    """
    Load plugins
    """
    commands = get_commands(include_aliases=False)
    for command_name in commands:
        cmdobj = commands[command_name]()
    return cmdobj


def print_help():
    """
    log command args and then display help
    """
    setup_commands()
    PARSER.print_help(sys.stderr)


def run(opts, args=None):
    """
    Run the target command
    """
    commands = get_commands()
    cmdobj = commands[opts.command]()
    try:
        return cmdobj.dispatch(opts, args)
    except KeyboardInterrupt:
        LOG.info("Interrupt")
        return os.EX_SOFTWARE
    except BaseException:
        print_help()
        return 1


def parse_sys(args):
    """
    Load plugins and parse command line
    """
    setup_commands()
    return PARSER.parse_known_args(args)
