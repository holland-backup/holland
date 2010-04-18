import os
import sys
import logging
from command import Command, option, StopOptionProcessing
from holland.core.plugin import get_commands

__all__ = [
    'Command',
    'option',
    'StopOptionProcessing',
    'run'
]

LOGGER = logging.getLogger(__name__)

def run(args=None):
    if args is None:
        args = sys.argv[1:]

    # Run the requested command
    commands = get_commands()

    if not args:
        args = ['help']

    command_name = args[0]

    if command_name not in commands:
        print >>sys.stderr, "No such command: %r" % command_name
        return os.EX_UNAVAILABLE
    else:
        cmdobj = commands[command_name]()
        try:
            return cmdobj.dispatch(args)
        except KeyboardInterrupt:
            LOGGER.info("Interrupt")
            return os.EX_SOFTWARE
        except Exception, e:
            LOGGER.debug("Command %r failed: %r", exc_info=True)
            print >>sys.stderr, "Command %r failed: %r" % (command_name, e)
            return os.EX_SOFTWARE
