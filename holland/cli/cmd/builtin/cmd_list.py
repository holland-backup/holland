"""Various list-* commands for holland.cli"""

import logging
from holland.core.plugin import iterate_plugins
from holland.cli.cmd.base import ArgparseCommand, argument

LOG = logging.getLogger(__name__)

class ListCommands(ArgparseCommand):
    name = 'list-commands'
    summary = 'List available holland commands'
    description = """
    List the available commands in holland with some
    information about each.
    """

    def execute(self, namespace):
        self.stderr("")
        self.stderr("Available commands:")
        commands = [plugin() for plugin in iterate_plugins('holland.commands')]
        commands.sort()
        for cmd in commands:
            aliases = ''
            if cmd.aliases:
                aliases = " (%s)" % ','.join(cmd.aliases)
            self.stderr("%-20s - %s", cmd.name + aliases, cmd.summary)
        return 0

    #@classmethod
    def plugin_info(cls):
        return PluginInfo(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)

class ListPlugins(ArgparseCommand):
    name = 'list-plugins'
    summary = 'List available holland plugins'
    description = """
    List available plugins in holland with some information about
    each

    Currently this lists the following plugin types:
    holland.backups     - backups plugins
    holland.commands    - command plugins
    """

    def execute(self, namespace):
        self.stderr("Available plugins:")
        for command in iterate_plugins('holland.commands'):
            command = command()
            self.stderr("[command] %-20s - %s", command.name, command.summary)
        for backup_plugin in iterate_plugins('holland.backup'):
            self.stderr("[backup]  %-20s - %s", backup_plugin.name, backup_plugin.summary)
        return 42

    #@classmethod
    def plugin_info(self):
        return PluginInfo(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)

class ListBackups(ArgparseCommand):
    name = 'list-backups'
    aliases = ['lb']
    summary = 'List spooled backups'
    description = '''
    List available backups in the configured backup-directory
    '''

    def execute(self, namespace):
        from holland.core import BackupSpool
        spool = BackupSpool(self.config['holland:backup']['backup-directory'])
        for backup in spool:
            self.stderr("-12s: %s", backup.name, backup.path)
        return 0

    #@classmethod
    def plugin_info(self):
        return PluginInfo(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)
