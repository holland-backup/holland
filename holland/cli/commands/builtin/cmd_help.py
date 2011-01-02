from holland.cli.commands.base import ArgparseCommand, argument
from holland.core.plugin import iterate_plugins

class Help(ArgparseCommand):
    name = 'help'
    summary = 'Show help for holland commands'
    description = """
    Show help for various commands in holland
    """

    arguments = [
        argument('command', nargs='?')
    ]

    #@property
    def epilog(self):
        result = []
        for cmd in iterate_plugins('holland.commands'):
            if cmd != self.__class__:
                cmd = cmd()
            else:
                cmd = self
                result.append("%-15s - %s" % (cmd.name, cmd.summary))
        return "\n".join(result)
    epilog = property(epilog)

    def execute(self, namespace):
        from holland.cli.commands import load_command
        if namespace.command:
            cmd = load_command('holland.commands', namespace.command)
        else:
            cmd = self

        self.stderr("%s", cmd.help())
        return 1

    def help(self):
        return self.parser.format_help()
