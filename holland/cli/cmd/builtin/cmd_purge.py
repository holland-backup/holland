"""Purge backups"""

from holland.cli.cmd.base import ArgparseCommand, argument

class Purge(ArgparseCommand):
    """Purge backup command"""
    name = 'purge'
    summary = 'Purge a backup'
    description = """
    Purge a backup
    """

    arguments = [
        argument('--all'),
        argument('--dry-run', '-n'),
        argument('--force'),
        argument('--execute', action='store_true'),
        argument('backups', nargs='*'),
    ]

    def execute(self, namespace):
        "Purge a backup"
        for backup in namespace.backups:
            try:
                spool.purge(backup)
            except:
                return 1

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
