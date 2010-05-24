import os, sys
import time
import errno
import fcntl
import logging
from holland.core.command import Command, option, run
from holland.core.backup import BackupRunner, BackupError
from holland.core.exceptions import BackupError
from holland.core.config import hollandcfg
from holland.core.spool import spool
from holland.core.util.fmt import format_interval

LOGGER = logging.getLogger(__name__)

class Backup(Command):
    """${cmd_usage}

    Backup the specified backupsets or all
    active backupsets specified in holland.conf

    ${cmd_option_list}

    """

    name = 'backup'

    aliases = [
        'bk'
    ]

    options = [
        option('--abort-immediately', action='store_true',
                help="Abort on the first backupset that fails."),
        option('--dry-run', '-n', action='store_true',
                help="Print backup commands without executing them."),
        option('--no-lock', '-f', action='store_true',
                help="Run even if another copy of Holland is running.")
    ]

    description = 'Run backups for active backupsets'

    def run(self, cmd, opts, *backupsets):
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]

        runner = BackupRunner(spool)
        runner.register_cb('pre-backup', run_purge)

        for name in backupsets:
            config = hollandcfg.backupset(name)
            runner.backup(name, config, opts.dry_run)

def run_purge(event, entry):
    print "run_purge: entry.name => %r" % entry.backupset
    run(["purge", "--backupset", entry.backupset])
