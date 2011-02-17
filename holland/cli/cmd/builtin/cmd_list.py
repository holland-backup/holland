"""Various list-* commands for holland.cli"""

import logging
from holland.core import BackupSpool, iterate_plugins
from holland.cli.cmd.base import ArgparseCommand, argument

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

    def execute(self, namespace, parser):
        """Run list-commands"""
        self.stderr("")
        self.stderr("Available commands:")
        commands = list(iterate_plugins('holland.commands'))
        commands.sort()
        for cmd in commands:
            aliases = ''
            if cmd.aliases:
                aliases = " (%s)" % ','.join(cmd.aliases)
            self.stderr("%-15s%-5s %s", cmd.name, aliases, cmd.summary)
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

    def execute(self, namespace, parser):
        self.stderr("Available plugins:")
        for group in ('backup', 'stream', 'hooks', 'commands'):
            plugin_list = list(iterate_plugins('holland.%s' % group))
            plugin_list.sort()
            for plugin in plugin_list:
                try:
                    info = plugin.plugin_info()
                except (SystemExit, KeyboardInterrupt):
                    raise
                except:
                    self.debug("Broken plugin %r - plugin_info() fails.",
                               plugin, exc_info=True)
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
    """List backups stored in the backup directory

    This command will look in the global backup directory (if one is
    specified) or in the directory specified by the ``--backup-directory``
    option.  If neither is provided this command will fail and exit with
    non-zero status.
    """

    name = 'list-backups'
    aliases = ['lb']
    summary = 'List spooled backups'
    description = '''
    List available backups in the configured backup-directory
    '''

    arguments = [
        argument('--backup-directory', '-d'),
    ]
    def execute(self, namespace, parser):
        """List backups in a backup spool"""
        backup_directory = namespace.backup_directory or \
                           self.config['holland']['backup-directory']

        if backup_directory is None:
            self.stderr("No backup-directory specified")
            return 1

        spool = BackupSpool(backup_directory)
        for backup in spool:
            self.stderr("%-12s: %s", backup.name, backup.path)
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
