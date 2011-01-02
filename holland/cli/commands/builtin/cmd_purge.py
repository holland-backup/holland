from holland.cli.commands.base import ArgparseCommand, argument

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
