from holland.cli.cmd.base import ArgparseCommand, argument

class Purge(ArgparseCommand):
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
        for backup in namespace.backups:
            try:
                spool.purge(backup)
            except:
                return 1

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
