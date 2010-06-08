import os
import sys
import time
import logging
from holland.core.plugin import PluginLoadError, load_backup_plugin
from holland.core.util.path import directory_size, disk_free
from holland.core.util.fmt import format_bytes, format_interval

LOG = logging.getLogger(__name__)

class BackupError(Exception):
    """Error during a backup"""

class BackupPlugin(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        raise NotImplementedError()

    def backup(self):
        raise NotImplementedError()

    def info(self):
        raise NotImplementedError()

    def configspec(self):
        raise NotImplementedError()


def load_plugin(name, config, path, dry_run):
        try:
            plugin_cls = load_backup_plugin(config['holland:backup']['plugin'])
        except KeyError, exc:
            raise BackupError("No plugin defined for backupset '%s'.", name) 
        except PluginLoadError, exc:
            raise BackupError(str(exc))


        try:
            return plugin_cls(name=name,
                              config=config,
                              target_directory=path,
                              dry_run=dry_run)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, exc:
            LOG.debug("Error while initializing %r : %s", 
                      plugin_cls, exc, exc_info=True)
            raise BackupError("Error initializing %s plugin: %s" % 
                              (config['holland:backup']['plugin'],
                               str(exc))
                             )


class BackupRunner(object):
    def __init__(self, spool):
        self.spool = spool
        self._registry = {}

    def register_cb(self, event, callback):
        self._registry.setdefault(event, []).append(callback)

    def apply_cb(self, event, *args, **kwargs):
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
        
        spool_entry = self.spool.add_backup(name)
        spool_entry.config.merge(config)
        spool_entry.validate_config()

        plugin = load_plugin(name,
                             spool_entry.config, 
                             spool_entry.path, 
                             dry_run)

        spool_entry.config['holland:backup']['start-time'] = time.time()
        self.apply_cb('pre-backup', spool_entry)

        if not dry_run:
            spool_entry.prepare()
    
        try:
            estimated_size = self.check_available_space(plugin)
            LOG.info("Starting backup[%s] via plugin %s",
                     spool_entry.name,
                     spool_entry.config['holland:backup']['plugin'])
            plugin.backup()
        except:
            spool_entry.config['holland:backup']['failed'] = True
        else:
            spool_entry.config['holland:backup']['failed'] = False

        spool_entry.config['holland:backup']['stop-time'] = time.time()
        if not dry_run and not spool_entry.config['holland:backup']['failed']:
            final_size = directory_size(spool_entry.path)
            LOG.info("Final on-disk backup size %s %.2f%% "
                     "of estimated size %s",
                     format_bytes(final_size),
                     (float(final_size) / estimated_size)*100.0,
                     format_bytes(estimated_size))
                     
            spool_entry.config['holland:backup']['on-disk-size'] = final_size
            spool_entry.flush()

        start_time = spool_entry.config['holland:backup']['start-time']
        stop_time = spool_entry.config['holland:backup']['stop-time']
        LOG.info("Backup completed in %s", 
                 format_interval(stop_time - start_time))

        self.apply_cb('post-backup', spool_entry)

        if sys.exc_info() != (None, None, None):
            LOG.error("Backup failed.  Cleaning up.")
            self.apply_cb('backup-failure', spool_entry)
            raise

    def check_available_space(self, plugin):
        estimated_bytes_required = plugin.estimate_backup_size()
        LOG.info("Estimated Backup Size: %s",
                 format_bytes(estimated_bytes_required))

        config = plugin.config['holland:backup']
        adjustment_factor = config['estimated-size-factor']
        adjusted_bytes_required = (estimated_bytes_required*adjustment_factor)
                                   
        if adjusted_bytes_required != estimated_bytes_required:
            LOG.info("Adjusting estimated size by %.2f to %s",
                     adjustment_factor,
                     format_bytes(adjusted_bytes_required))

        available_bytes = disk_free(self.spool.path)
        if available_bytes <= adjusted_bytes_required:
            raise BackupError("Insufficient Disk Space. "
                              "%s required, but only %s available on %s" %
                              (format_bytes(adjusted_bytes_required),
                               format_bytes(available_bytes),
                               self.spool.path))
        return estimated_bytes_required
