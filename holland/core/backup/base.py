"""
Define how backup plugins will be called
"""

import os
import sys
import time
import errno
import logging
from holland.core.plugin import PluginLoadError, load_backup_plugin
from holland.core.util.path import directory_size, disk_free
from holland.core.util.fmt import format_bytes, format_interval

MAX_SPOOL_RETRIES = 5

LOG = logging.getLogger(__name__)

class BackupError(Exception):
    """Error during a backup"""

class BackupPlugin(object):
    """
    Define a backup plugin
    """
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        """
        placeholad
        """
        raise NotImplementedError()

    def backup(self):
        """
        placeholad
        """
        raise NotImplementedError()

    def info(self):
        """
        placeholad
        """
        raise NotImplementedError()

    def configspec(self):
        """
        placeholad
        """
        raise NotImplementedError()


def load_plugin(name, config, path, dry_run):
    """
    Method to load plugins
    """
    try:
        plugin_cls = load_backup_plugin(config['holland:backup']['plugin'])
    except KeyError as exc:
        raise BackupError("No plugin defined for backupset '%s'.", name)
    except PluginLoadError as exc:
        raise BackupError(str(exc))

    try:
        return plugin_cls(name=name,
                          config=config,
                          target_directory=path,
                          dry_run=dry_run)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        LOG.debug("Error while initializing %r : %s",
                  plugin_cls, exc, exc_info=True)
        raise BackupError("Error initializing %s plugin: %s" %
                          (config['holland:backup']['plugin'],
                           str(exc))
                         )


class BackupRunner(object):
    """
    Run backup
    """
    def __init__(self, spool):
        self.spool = spool
        self._registry = {}

    def register_cb(self, event, callback):
        """
        create callback
        """
        self._registry.setdefault(event, []).append(callback)

    def apply_cb(self, event, *args, **kwargs):
        """
        Catch Callback
        """
        for callback in self._registry.get(event, []):
            try:
                callback(event, *args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                raise BackupError(str(sys.exc_info()[1]))

    def backup(self, name, config, dry_run=False):
        """Run a backup for the named backupset using the provided
        configuration

        :param name: name of the backupset
        :param config: dict-like object providing the backupset configuration

        :raises: BackupError if a backup fails
        """
        for i in range(MAX_SPOOL_RETRIES):
            try:
                spool_entry = self.spool.add_backup(name)
                break
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise BackupError("Failed to create spool: %s" % exc)
                LOG.debug("Failed to create spool.  Retrying in %d seconds.", i+1)
                time.sleep(i+1)
        else:
            raise BackupError("Failed to create a new backup directory for %s" % name)

        spool_entry.config.merge(config)
        spool_entry.validate_config()

        if dry_run:
            # always purge the spool
            self.register_cb('post-backup',
                             lambda *args, **kwargs: spool_entry.purge())

        plugin = load_plugin(name,
                             spool_entry.config,
                             spool_entry.path,
                             dry_run)

        spool_entry.config['holland:backup']['start-time'] = time.time()
        spool_entry.flush()
        self.apply_cb('before-backup', spool_entry)

        try:
            estimated_size = self.check_available_space(plugin, spool_entry, dry_run)
            LOG.info("Starting backup[%s] via plugin %s",
                     spool_entry.name,
                     spool_entry.config['holland:backup']['plugin'])
            plugin.backup()
        except KeyboardInterrupt:
            LOG.warning("Backup aborted by interrupt")
            spool_entry.config['holland:backup']['failed'] = True
            raise
        except Exception as ex:
            LOG.warning(ex)
            spool_entry.config['holland:backup']['failed'] = True
            raise
        else:
            spool_entry.config['holland:backup']['failed'] = False

        spool_entry.config['holland:backup']['stop-time'] = time.time()
        if not dry_run and not spool_entry.config['holland:backup']['failed']:
            final_size = float(directory_size(spool_entry.path))
            LOG.info("Final on-disk backup size %s", format_bytes(final_size))
            if estimated_size > 0:
                LOG.info("%.2f%% of estimated size %s",
                         (final_size / estimated_size)*100.0,
                         format_bytes(estimated_size))

            spool_entry.config['holland:backup']['on-disk-size'] = final_size
            spool_entry.flush()

        start_time = spool_entry.config['holland:backup']['start-time']
        stop_time = spool_entry.config['holland:backup']['stop-time']

        if spool_entry.config['holland:backup']['failed']:
            LOG.error("Backup failed after %s",
                      format_interval(stop_time - start_time))
        else:
            LOG.info("Backup completed in %s",
                     format_interval(stop_time - start_time))


        if dry_run:
            spool_entry.purge()

        if sys.exc_info() != (None, None, None):
            self.apply_cb('failed-backup', spool_entry)
            raise BackupError("Failed backup: %s" % name)
        else:
            self.apply_cb('after-backup', spool_entry)

    def free_required_space(self, name, required_bytes, dry_run=False):
        """Attempt to free at least ``required_bytes`` of old backups from a backupset

        :param name: name of the backupset to free space from
        :param required_bytes: integer number of bytes required for the backupset path
        :param dry_run: if true, this will only generate log messages but won't actually free space
        :returns: bool; True if freed or False otherwise
        """
        LOG.info("Insufficient disk space for adjusted estimated backup size: %s",
                 format_bytes(required_bytes))
        LOG.info("purge-on-demand is enabled. Discovering old backups to purge.")
        available_bytes = disk_free(os.path.join(self.spool.path, name))
        to_purge = {}
        for backup in self.spool.list_backups(name):
            backup_size = directory_size(backup.path)
            LOG.info("Found backup '%s': %s",
                     backup.path, format_bytes(backup_size))
            available_bytes += backup_size
            to_purge[backup] = backup_size
            if available_bytes > required_bytes:
                break
        else:
            LOG.info("Purging would only recover an additional %s",
                     format_bytes(sum(to_purge.values())))
            LOG.info("Only %s total would be available, but the current "
                     "backup requires %s",
                     format_bytes(available_bytes),
                     format_bytes(required_bytes))
            return False

        purge_bytes = sum(to_purge.values())
        LOG.info("Found %d backups to purge which will recover %s",
                 len(to_purge), format_bytes(purge_bytes))

        for backup in to_purge:
            if dry_run:
                LOG.info("Would purge: %s", backup.path)
            else:
                LOG.info("Purging: %s", backup.path)
                backup.purge()
        LOG.info("%s now has %s of available space",
                 os.path.join(self.spool.path, name),
                 format_bytes(disk_free(os.path.join(self.spool.path, name))))
        return True

    def check_available_space(self, plugin, spool_entry, dry_run=False):
        """
        calculate available space before performing backup
        """
        available_bytes = disk_free(spool_entry.path)

        estimated_bytes_required = float(plugin.estimate_backup_size())
        LOG.info("Estimated Backup Size: %s",
                 format_bytes(estimated_bytes_required))

        config = plugin.config['holland:backup']
        adjustment_factor = float(config['estimated-size-factor'])
        adjusted_bytes_required = (estimated_bytes_required*adjustment_factor)

        if adjusted_bytes_required != estimated_bytes_required:
            LOG.info("Adjusting estimated size by %.2f to %s",
                     adjustment_factor,
                     format_bytes(adjusted_bytes_required))

        if available_bytes <= adjusted_bytes_required:
            if not (config['purge-on-demand'] and
                    self.free_required_space(spool_entry.backupset,
                                             adjusted_bytes_required,
                                             dry_run)):
                msg = ("Insufficient Disk Space. %s required, "
                       "but only %s available on %s") % (
                           format_bytes(adjusted_bytes_required),
                           format_bytes(available_bytes),
                           self.spool.path)
                LOG.error(msg)
                if not dry_run:
                    raise BackupError(msg)
        return float(estimated_bytes_required)
