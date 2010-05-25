import os
import sys
import logging
import readline
import itertools
from holland.core.command import Command, option
from holland.core.config import hollandcfg, ConfigError
from holland.core.spool import spool, CONFIGSPEC
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

    options = [
        option('--dry-run', '-n', action='store_true', default=True,
                help="Print what would be purged without actually purging"),
        option('--all', '-a', action='store_true', default=False,
                help="When purging a backupset purge everything rather than "
                     "using the retention count from the active configuration"),
        option('--force', '-f', action='store_true', default=False,
               help="Do not prompt for confirmation")
    ]

    description = 'Purge the requested job runs'
    
    def run(self, cmd, opts, *backups):
        error = 0

        for name in backups:
            if '/' not in name:
                backupset = spool.find_backupset(name)
                if not backupset:
                    LOG.error("Failed to find backupset '%s'", name)
                    error = 1
                    continue
                purge_backupset(backupset, opts.force)
            else:
                backup = spool.find_backup(name)
                if not backup:
                    LOG.error("Failed to find single backup '%s'", name)
                    error = 1
                    continue
                purge_backup(backup, opts.force)
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
            config = hollandcfg.backupset(backupset.name)
            config.validate_config(CONFIGSPEC)
        except (IOError, ConfigError), exc:
            LOG.error("Failed to load backupset '%s': %s", backupset.name, exc)
            LOG.error("Aborting, because I could not tell how many backups to "
                      "preserve.")
            LOG.error("You can still purge the backupset by using the --all "
                      "option or specifying specific backups to purge")
            return 1

    LOG.info("Retaining %d backups", retention_count)
    backups = []
    bytes = 0
    backup_list = backupset.list_backups(reverse=True)
    for backup in itertools.islice(backup_list, retention_count, None):
        backups.append(backup)
        config = backup.config['holland:backup']
        bytes += int(config['on-disk-size'])

    if not force:
        LOG.info("Would purge backupset %s", backupset.name)
        LOG.info("    %d total backups", len(backup_list))
        LOG.info("    %d backups would be retained", len(backup_list) - len(backups))
        LOG.info("    %d backups would be purged", len(backups))
        LOG.info("    %s total space would be freed", format_bytes(bytes))
    else:
        for backup in backupset.purge(retention_count):
            LOG.info("Purged %s", backup.name)   

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
