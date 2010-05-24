import os
import sys
import time
from holland.core.plugin import PluginLoadError, load_backup_plugin

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

        plugin = load_plugin(name, config, spool_entry.path, dry_run)

        spool_entry.config['holland:backup']['start-time'] = time.time()
        self.apply_cb('pre-backup', spool_entry)

        if not dry_run:
            spool_entry.prepare()

        try:
            plugin.backup()
        except:
            spool_entry.config['holland:backup']['failed'] = True
        else:
            spool_entry.config['holland:backup']['failed'] = False

        spool_entry.config['holland:backup']['start-time'] = time.time()

        if not dry_run:
            spool_entry.flush()

        self.apply_cb('post-backup', spool_entry)

        if sys.exc_info() != (None, None, None):
            raise
