"""Holland CLI pluggable command support"""
import logging
from holland.core.plugin import iterate_plugins
from holland.cli.cmd.base import *
from holland.cli.cmd.builtin import *
from holland.cli.cmd.error import CommandNotFoundError

LOG = logging.getLogger(__name__)

def load_command(group, name, *args, **kwargs):
    commands = [command for command in iterate_plugins(group)]
    for cmd in commands:
        if cmd.matches(name):
            return cmd(*args, **kwargs)
    raise CommandNotFoundError(name)
