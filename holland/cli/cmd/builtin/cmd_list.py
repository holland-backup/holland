"""Various list-* commands for holland.cli"""

import sys
import logging
from holland.core.plugin import iterate_plugins
from holland.cli.cmd.base import ArgparseCommand

LOG = logging.getLogger(__name__)

class ListCommands(ArgparseCommand):
    """List available commands"""

    name = 'list-commands'
    aliases = ['lc']
    summary = 'List available holland commands'
    description = """
    List the available commands in holland with some
    information about each.
    """

    def execute(self, namespace):
        """Run list-commands"""
        self.stderr("")
        self.stderr("Available commands:")
        commands = [plugin(self.parent_parser, self.config)
                    for plugin in iterate_plugins('holland.commands')]
        commands.sort()
        for cmd in commands:
            aliases = ''
            if cmd.aliases:
                aliases = " (%s)" % ','.join(cmd.aliases)
            self.stderr("%-20s - %s", cmd.name + aliases, cmd.summary)
        return 0

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

class ListPlugins(ArgparseCommand):
    """List available plugins"""

    name = 'list-plugins'
    aliases = ['lp']
    summary = 'List available holland plugins'
    description = """
    List available plugins in holland with some information about
    each

    Currently this lists the following plugin types:
    holland.backups     - backups plugins
    holland.stream      - output filtering plugins
    holland.hooks       - hook plugins
    holland.commands    - command plugins
    """

    def execute(self, namespace):
        self.stderr("Available plugins:")
        for group in ('backup', 'stream', 'hooks', 'commands'):
            for plugin in iterate_plugins('holland.%s' % group):
                try:
                    info = plugin.plugin_info()
                except:
                    self.stderr("plugin %r plugin_info failed :(", plugin)
                    self.stderr("%r", sys.exc_info())
                    continue
                self.stderr("%-10s %-20s - %s", "[%s]" % group,
                            info['name'],
                            info['summary'])
        return 0

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
