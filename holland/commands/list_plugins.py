"""
Print list of installed plugins
"""

import sys
from holland.core.command import Command
from holland.core.plugin import iter_plugins

class ListPlugins(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Lists installed plugins
    """
    name = 'list-plugins'
    aliases = [
        'lp'
    ]
    description = 'List installed plugins'

    args = []
    kargs = []

    @staticmethod
    def print_table(table):
        """
        Format and print table
        """
        header = table[0]
        rest = table[1:]
        fmt = "%-12s %-15s %-9s %-16s %s"
        print(fmt % tuple(header))
        print("-"*80)
        for row in rest:
            print(fmt % tuple(row))

    def run(self, cmd, opts, *args):
        if args:
            print("The list-plugin command takes no arguments", file=sys.stderr)
        table_header = ["Plugin-Type", "Plugin-Name", "Version", "Author", "Summary"]
        table = []

        for plugin, metainfo in iter_plugins('holland.backup'):
            row = ['backup', plugin]
            for key in ['version', 'author', 'summary']:
                row.append(metainfo.get(key, '-'))
            table.append(row)

        for plugin, metainfo in iter_plugins('holland.commands'):
            row = ['command', plugin]
            for key in ['version', 'author', 'summary']:
                row.append(metainfo.get(key, '-'))
            table.append(row)
        table.sort()
        table.insert(0, table_header)
        if len(table) == 1:
            print("No Plugins Found")
        else:
            self.print_table(table)

        return 0
