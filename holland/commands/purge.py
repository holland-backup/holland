"""
Command to delete old backups
"""

import logging
import itertools
from holland.core.command import Command
from holland.core.config import HOLLANDCFG, ConfigError
from holland.core.spool import SPOOL, CONFIGSPEC
from holland.core.util.fmt import format_bytes

LOG = logging.getLogger(__name__)

class Purge(Command):
    """${cmd_usage}

    Purge the requested job runs

    ${cmd_option_list}

    """

    name = 'purge'

    aliases = [
        'pg'
    ]

    args = [
        ['--dry-run', '-n'],
        ['--all', '-a'],
        ['--force', '-f'],
        ['--execute']
    ]

    kargs = [
        {
            'action':'store_true',
            'dest':'force',
            'default':False,
            'help':"Print what would be purged without actually purging"
        },
        {
            'action':'store_true',
            'default':False,
            'help':"When purging a backupset purge everything rather than \
                     using the retention count from the active configuration",
        },
        {
            'action':'store_true',
            'default':False,
            'help':"Execute the purge (disable dry-run). Alias for --execute"
        },
        {
            'action':'store_true',
            'dest':'force',
            'help':"Execute the purge (disable dry-run)"
        }
    ]

    description = 'Purge the requested job runs'

    def run(self, cmd, opts, *backups):
        error = 0

        if not backups:
            LOG.info("No backupsets specified - using backupsets from %s",
                     HOLLANDCFG.filename)
            backups = HOLLANDCFG.lookup('holland.backupsets')

        if not backups:
            LOG.warning("Nothing to purge")
            return 0

        if not opts.force:
            LOG.warning("Running in dry-run mode.  Use --execute to do a real purge.")

        for name in backups:
            if '/' not in name:
                backupset = SPOOL.find_backupset(name)
                if not backupset:
                    LOG.error("Failed to find backupset '%s'", name)
                    error = 1
                    continue
                purge_backupset(backupset, opts.force, opts.all)
            else:
                backup = SPOOL.find_backup(name)
                if not backup:
                    LOG.error("Failed to find single backup '%s'", name)
                    error = 1
                    continue
                purge_backup(backup, opts.force)
                if opts.force:
                    SPOOL.find_backupset(backup.backupset).update_symlinks()
        return error

def purge_backupset(backupset, force=False, all_backups=False):
    """Purge a whole backupset either entirely or per the configured
    retention count

    :param backupset: Backupset object to purge
    :param force: Force the purge - this is not a dry-run
    :param all_backupsets: purge all backups regardless of configured
                           retention count
    """
    if all_backups:
        retention_count = 0
    else:
        try:
            config = HOLLANDCFG.backupset(backupset.name)
            config.validate_config(CONFIGSPEC, suppress_warnings=True)
        except (IOError, ConfigError) as exc:
            LOG.error("Failed to load backupset '%s': %s", backupset.name, exc)
            LOG.error("Aborting, because I could not tell how many backups to "
                      "preserve.")
            LOG.error("You can still purge the backupset by using the --all "
                      "option or specifying specific backups to purge")
            return 1
        retention_count = config['holland:backup']['backups-to-keep']

    LOG.info("Evaluating purge for backupset %s", backupset.name)
    LOG.info("Retaining up to %d backup%s",
             retention_count, 's'[0:bool(retention_count)])
    backups = []
    size = 0
    backup_list = backupset.list_backups(reverse=True)
    for backup in itertools.islice(backup_list, retention_count, None):
        backups.append(backup)
        config = backup.config['holland:backup']
        size += int(config['on-disk-size'])

    LOG.info("    %d total backups", len(backup_list))
    for backup in backup_list:
        LOG.info("        * %s", backup.path)
    LOG.info("    %d backups to keep", len(backup_list) - len(backups))
    for backup in backup_list[0:-len(backups)]:
        LOG.info("        + %s", backup.path)
    LOG.info("    %d backups to purge", len(backups))
    for backup in backups:
        LOG.info("        - %s", backup.path)
    LOG.info("    %s total to purge", format_bytes(size))

    if force:
        count = 0
        for backup in backupset.purge(retention_count):
            count += 1
            LOG.info("Purged %s", backup.name)
        if count == 0:
            LOG.info("No backups purged.")
        else:
            LOG.info("Purged %d backup%s", count, 's'[0:bool(count)])
    else:
        LOG.info("Skipping purge in dry-run mode.")
    backupset.update_symlinks()

def purge_backup(backup, force=False):
    """Purge a single backup

    :param backup: Backup object to purge
    :param force: Force the purge - this is not a dry-run
    """
    if not force:
        config = backup.config['holland:backup']
        LOG.info("Would purge single backup '%s' %s",
                 backup.name,
                 format_bytes(int(config['on-disk-size'])))
    else:
        backup.purge()
        LOG.info("Purged %s", backup.name)
