"""Various list-* commands for holland.cli"""

import textwrap
import logging
from holland.core import BackupSpool, iterate_plugins
from holland.core.util import format_bytes, format_datetime
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
        self.stdout("")
        self.stdout("Available commands:")
        commands = list(iterate_plugins('holland.commands'))
        commands.sort()
        for cmd in commands:
            aliases = ''
            if cmd.aliases:
                aliases = " (%s)" % ','.join(cmd.aliases)
            self.stdout("%-15s%-5s %s", cmd.name, aliases, cmd.summary)
        return 0

    def plugin_info(self):
        return dict(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )

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
        self.stdout("%-12s %-14s %11s", 'Plugin Type', 'Name', 'Description')
        self.stdout("%12s %14s %11s", "="*12, "="*14, "="*11)
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
                wrap = textwrap.wrap
                summary = wrap(info.get('summary', ''),
                               initial_indent=' '*28,
                               subsequent_indent=' '*28,
                               width=79)
                self.stdout("%-12s %-14s %s", group,
                            plugin.name,
                            '\n'.join(summary).lstrip())
        return 0

    def plugin_info(self):
        return dict(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )

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
        backupsets = spool.list_backupsets() or ['']
        padding = max([len(name) for name in backupsets]) + 1
        self.stdout("%36s %*s %10s %5s",
                    "Created", padding, "Backupset", "Size", "Path")
        self.stdout("%36s %s %10s %s", "-"*36, "-"*padding, "-"*10, "-"*5)
        for backup in spool:
            self.stdout("<Created %s> %*s %10s %s",
                        format_datetime(backup.timestamp), padding, backup.name,
                        "[%s]" % format_bytes(backup.size()), backup.path)
        return 0

    def plugin_info(self):
        return dict(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
