from __future__ import print_function
import os
import sys
# for python2.3 support
if sys.version_info[:2] < (2, 4):
    from sets import Set as set
from holland.core.command.command import Command, option
from holland.core.plugin import get_commands
from holland.core.cmdshell import parser

class Help(Command):
    """${cmd_usage}

    ${cmd_option_list}

    """
    name = 'help'
    aliases = [
        'h'
    ]
    options = [
        option('-v', '--verbose', action='store_true',
                help="Display more information")
    ]
    description = 'Show help for a command'
    def run(self, cmd, opts, command=None):

        commands = get_commands()
        if not command:
            print("No command specified", file=sys.stderr)
            parser.print_help()

            if not commands:
                print("No available commands", file=sys.stderr)
            else:
                print("Available Commands:")
                commands = list(set(commands.values()))
                commands.sort(key = lambda x: x.name)
                for cls in commands:
                    if cls.aliases:
                        cmdname = "%-13s (%s)" % (cls.name, ','.join(cls.aliases))
                    else:
                        cmdname = cls.name
                    print("   %-19s  %s" % (cmdname, cls.description))

            return 1

        if not command in commands:
            print("No such command: %r" % command, file=sys.stderr)
            return os.EX_TEMPFAIL

        cmdinst = commands[command]()
        print(cmdinst.help())
