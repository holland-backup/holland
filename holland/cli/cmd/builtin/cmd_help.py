"""holland help command"""

from holland.cli.cmd.base import ArgparseCommand, argument
from holland.cli.cmd.error import CommandNotFoundError
from holland.core.plugin import iterate_plugins

class Help(ArgparseCommand):
    """Holland help subcommand"""

    name = 'help'
    summary = 'Show help for holland commands'
    description = """
    Show help for various commands in holland
    """

    arguments = [
        argument('command', nargs='?')
    ]

    _add_help = False

    #@property
    def epilog(self):
        """List available commands in the help subcommand epilog"""
        result = []
        commands = list(iterate_plugins('holland.commands'))
        commands.sort()
        for cmd in commands:
            aliases = ''
            if cmd.aliases:
                aliases = " (%s)" % ','.join(cmd.aliases)
            result.append("%-15s%-5s %s" % (cmd.name, aliases, cmd.summary))
        return "\n".join(result)
    epilog = property(epilog)

    def execute(self, namespace, parser):
        """Run the help command"""
        if namespace.command:
            try:
                cmd = self.load(namespace.command)
            except CommandNotFoundError:
                self.stderr("No command '%s'", namespace.command)
                return 1
        else:
            cmd = self

        self.stderr("%s", cmd.help())
        return 0

    def plugin_info(self):
        """Provide info about this plugin"""
        return dict(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
