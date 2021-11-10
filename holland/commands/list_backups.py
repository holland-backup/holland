"""
Define List Backup Command
"""

import re
import sys

from holland.core.command import Command
from holland.core.plugin import load_backup_plugin
from holland.core.spool import SPOOL


class ListBackups(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Lists available backups
    """

    name = "list-backups"
    aliases = ["lb"]
    description = "List available backups"
    args = [["-v", "--verbose"]]
    kargs = [{"action": "store_true", "help": "Verbose output"}]

    @staticmethod
    def print_table(table):
        """
        Format data and print data
        """
        rest = table[1:]
        fmt = "%-28s %-9s %-16s %s"
        for row in rest:
            print(fmt % tuple(row))

    def run(self, cmd, opts, *args):
        """
        get backup informantion and call print table
        """
        if args:
            print("The list-backup command takes no arguments", file=sys.stderr)
        backup_list = list(SPOOL.list_backups())
        if not backup_list:
            print("No backups")
            return 0

        backupsets_seen = []
        for backup in backup_list:
            if backup.backupset not in backupsets_seen:
                backupsets_seen.append(backup.backupset)
                print("Backupset[%s]:" % (backup.backupset))
            # Read the backup.conf
            backup.load_config()
            plugin_name = backup.config.get("holland:backup", {})["plugin"]
            if not plugin_name:
                print("Skipping broken backup: %s" % backup.name)
                continue
            print("\t%s" % backup.name)
            if opts.verbose:
                print("\t", backup.info())
                plugin = load_backup_plugin(plugin_name)
                plugin = plugin(backup.backupset, backup.config, backup.path)
                if hasattr(plugin, "info"):
                    plugin_info = plugin.info()
                    rec = re.compile(r"^", re.M)
                    print(rec.sub("\t\t", plugin_info))

        return 0
