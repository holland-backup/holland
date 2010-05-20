"""Holland Backup Module"""

import os
import sys
import time
import pprint
import logging
from holland.core.exceptions import BackupError
from holland.core.util.path import disk_free, directory_size
from holland.core.util.fmt import format_interval, format_bytes
from holland.core.plugin import load_backup_plugin, PluginLoadError
from holland.core.config import load_backupset_config
from holland.core.spool import spool

LOGGER = logging.getLogger(__name__)

def load_plugin(cfg):
    provider = cfg.lookup('holland:backup.plugin')

    LOGGER.info("Loading Backup Plugin '%s'", provider)
    if not provider:
        raise IOError("No provider defined")
    try:
        plugincls = load_first_entrypoint("holland.backup", provider)
    except PluginLoadError, e:
        raise LookupError("Failed to load plugin %r: %s" % (provider, e))

    if not plugincls:
        raise LookupError("Plugin %r not found" % ('holland.backup.' + provider))
    return plugincls

def _find_existing_parent(path):
    while not os.path.exists(path):
        path, _ = os.path.split(path)
        if _ == '':
            break

    return path 

def verify_space(required_space, target_directory):
    available_space = disk_free(_find_existing_parent(target_directory))
    if required_space >= available_space:
        LOGGER.error("Insufficient Disk Space.  Required: %s Available: %s", 
                    format_bytes(required_space), 
                    format_bytes(available_space))
        raise BackupError("%s required but only %s available on %s" % \
                            (format_bytes(required_space),
                            format_bytes(available_space),
                            target_directory))

def purge_old_backups(backupset, backups_to_keep=1, exclude=()):
    assert backups_to_keep > 0
    LOGGER.info("Purging old backups from backupset '%s'", backupset)
    backupset = spool.find_backupset(backupset)
    backups = [bk for bk in backupset.list_backups(reverse=True) 
                if bk not in exclude]
    # Make sure we keep holland:backup.backups-to-keep
    LOGGER.info("Found %d backups.  Keeping %d", len(backups), backups_to_keep)
    purge_list = []
    for backup in backups:
        if backup.config.get('holland:backup',{}).get('stop-time', 0) == 0:
            LOGGER.debug("Purging broken backup")
            purge_list.insert(0, backup)
        elif backups_to_keep == 0:
            LOGGER.debug("Purging old backup")
            purge_list.insert(0, backup)
        else:
            LOGGER.debug("Retaining backup %s", backup.name)
            backups_to_keep -= 1

    if not purge_list:
        LOGGER.info("No backups to purge")
    else:
        for backup in purge_list:
            LOGGER.info("Purging %s", backup.name)
            backup.purge()

def backup(backupset_name, dry_run=False, skip_purge=False):


    # May raise a ConfigError if not backupset is found
    LOGGER.info("Loading config for backupset %s", backupset_name)
    try:
        backupset_cfg = load_backupset_config(backupset_name)
    except IOError, e:
        LOGGER.error("Failed to load backupset %s: %s", backupset_name, e)
        raise BackupError("Aborting due to previous errors.")
    except SyntaxError, e:
        LOGGER.error("Failed to load backupset config %r [%s]. %s", 
                        backupset_name, 
                        e.config.filename,
                        e
                    )
        LOGGER.error("Bad line appears to be '%s'", e.line)
        raise BackupError("Aborting due to previous errors.")

    # May raise a PluginError if the plugin could not be loaded
    LOGGER.info("Loading plugin %s", backupset_cfg.lookup('holland:backup.plugin'))
    try:
        plugincls = load_backup_plugin(backupset_cfg.lookup('holland:backup.plugin'))
    except PluginLoadError, e:
        LOGGER.error("Failed to load plugin %s: %s", 
                     backupset_cfg.lookup('holland:backup.plugin'), e)
        raise BackupError(e)
    
    # Possible IOError here if we cannot write to spool
    # Don't create the directory in dry-run mode
    backup_job = spool.add_backup(backupset_name)
    LOGGER.info("Prepared backup spool %s", backup_job.path)
    # Always merge in the backupset config to the backup-local config
    LOGGER.debug("Merging backupset config into local backup.conf config")
    backup_job.config.merge(backupset_cfg)
    backup_job.validate_config()

    # Plugin may fail to initialize due to programming error
    LOGGER.debug("Initializing backup plugin instance")
    try:
        plugin = plugincls(backupset_name, backup_job.config, backup_job.path, dry_run)
    except Exception, e:
        LOGGER.debug("Failed to instantiate backup plugin %s: %s",
                     backupset_cfg.lookup('holland:backup.plugin'),
                     e, exc_info=True)
        raise BackupError("Failed to initialize backup plugin %s: %s" % 
                          (backupset_cfg.lookup('holland:backup.plugin'), e))

    # Plugin may raise exception due to programming error, be careful
    estimated_size = plugin.estimate_backup_size()
    estimate_factor = backup_job.config['holland:backup']['estimated-size-factor']
    adjusted_estimate = estimate_factor*estimated_size

    LOGGER.info("Estimated Backup Size: %s",
                 format_bytes(estimated_size)
               )

    if adjusted_estimate != estimated_size:
        LOGGER.info("Using estimated-size-factor=%.2f and adjusting estimate to %s",
                     estimate_factor,
                     format_bytes(adjusted_estimate)
                   )
    # Save the estimated size in the backup.conf
    backup_job.config['holland:backup']['estimated-size'] = estimated_size
    try:
        verify_space(adjusted_estimate, backup_job.path)
    except BackupError, exc:
        if not dry_run:
            raise

    if not dry_run:
        LOGGER.info("Purging old backup jobs")
        purge_old_backups(backupset_name, 
                          backup_job.config.lookup('holland:backup.backups-to-keep'),
                          exclude=[backup_job])

    # Start backup
    backup_job.config['holland:backup']['start-time'] = time.time()
    # initialize spool directory
    if not dry_run:
        backup_job.prepare()

    exc = None
    try:
        LOGGER.info("Starting backup[%s] via plugin %s", 
                    backup_job.name,
                    backupset_cfg.lookup('holland:backup.plugin'))
        plugin.backup()
    except KeyboardInterrupt:
        exc = BackupError("Interrupted")
    except Exception, exc:
        if not isinstance(exc, BackupError):
            LOGGER.debug("Unexpected exception when running backups.", exc_info=True)
            exc = BackupError(exc)

    backup_job.config['holland:backup']['stop-time'] = time.time()
    backup_interval = (backup_job.config['holland:backup']['stop-time'] -
                       backup_job.config['holland:backup']['start-time'])
    if dry_run:
        LOGGER.info("Dry-run completed in %s",
                    format_interval(backup_interval))
    else:
        LOGGER.info("Backup completed in %s", 
                    format_interval(backup_interval))

    if not dry_run and exc is None:
        final_size = directory_size(backup_job.path)
        LOGGER.info("Final on-disk backup size: %s %.2f%% of estimated size %s", 
                    format_bytes(final_size), 
                    estimated_size and 100*(float(final_size)/estimated_size) or 0.0,
                    format_bytes(estimated_size))
        backup_job.config['holland:backup']['on-disk-size'] = final_size
        LOGGER.debug("Flushing backup job")
        backup_job.flush()

    if exc is not None:
        if backup_job.config['holland:backup']['auto-purge-failures'] is True:
            LOGGER.warning("Purging this backup (%s) due to failure", backup_job.name)
            backup_job.purge()
        raise
