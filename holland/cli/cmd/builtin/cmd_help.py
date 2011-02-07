"""holland help command"""

from holland.cli.cmd.base import ArgparseCommand, argument
from holland.core.plugin import iterate_plugins, load_plugin

class Help(ArgparseCommand):
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
        if namespace.command:
            cmd = self.load(namespace.command)
        else:
            cmd = self

        self.stderr("%s", cmd.help())
        return 1

    #@classmethod
    def plugin_info(cls):
        return dict(
            name=cls.name,
            summary=cls.summary,
            description=cls.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)
