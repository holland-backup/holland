import logging
from holland.core.command import Command, option
from holland.core.plugin import load_first_entrypoint
from holland.core.spool import spool

LOGGER = logging.getLogger(__name__)

class Restore(Command):
    """${cmd_usage}

    Restore data from an existing Holland backup

    The actual restore is delegated to the backup plugin that
    created the backup. 

    Example:
    holland ${cmd_name} some-backup --help

    # Example restore for a mysqldump based backup
    holland ${cmd_name} some-backup --table mysql.proc 

    ${cmd_option_list}
        
    """

    name = 'restore'

    aliases = [
        're'
    ]

    options = [
        option('--dry-run', '-n', action='store_true',
                help="Print what restore actually would do without actually running the restore")
    ]

    description = 'Restore data from an existing Holland Backup'
    def __init__(self):
        Command.__init__(self)
        self.optparser.disable_interspersed_args()

    def run(self, cmd, opts, backup_name, *restore_options):
        backup = spool.find_backup(backup_name)
        if not backup:
            logging.error("No backup found named %s", backup_name)
            return 1
        config = backup.config
        plugin_name = config.get('holland:backup', {}).get('plugin')
        plugin = load_first_entrypoint('holland.restore', plugin_name)(backup)
        plugin.dispatch([plugin_name]  + list(restore_options))
        return 1
