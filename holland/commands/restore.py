"""
Unused restore command
"""

import logging
from holland.core.command import Command
from holland.core.plugin import load_first_entrypoint
from holland.core.spool import SPOOL

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

    name = "restore"

    aliases = ["re"]

    args = ["--dry-run", "-n"]
    kargs = [
        {
            "help": "Print what restore actually would do without actually running the restore"
        }
    ]

    description = "Restore data from an existing Holland Backup"

    def __init__(self):
        Command.__init__(self)
        self.optparser.disable_interspersed_args()

    def run(self, cmd, opts, *args):
        backup = SPOOL.find_backup(args[0])
        if not backup:
            logging.error("No backup found named %s", args[0])
            return 1
        config = backup.config
        plugin_name = config.get("holland:backup", {}).get("plugin")
        plugin = load_first_entrypoint("holland.restore", plugin_name)(backup)
        plugin.dispatch([plugin_name] + list(args))
        return 1
