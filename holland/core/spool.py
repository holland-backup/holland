"""
Utilities to manage spool directory
"""

import os
import sys
import time
import shutil
import logging
import itertools
from holland.core.config import BaseConfig

LOGGER = logging.getLogger(__name__)

def timestamp_dir(when=None):
    """
    Returns a directory named after the specified time or
    the current time, if no specific time is given
    """
    if when is None:
        when = time.time()
    return time.strftime("%Y%m%d_%H%M%S", time.localtime(when))
 
class Spool(object):
    """
    A directory spool where backups are saved
    """
    def __init__(self, path=None):
        self.path = path or '/var/spool/holland'
 
    def find_backup(self, name):
        """
        Find a the specified backup, if it exists. If the backup does
        not exist, returns None

        The backup name must be in <backupset>/<timestamp> format
        """
        try:
            backupset_name, timestamp = name.split('/')
            backupset = self.find_backupset(backupset_name)
            if backupset:
                return backupset.find_backup(timestamp)
            else:
                return None
        except ValueError, e:
            LOGGER.warning("Invalid backup name: %s", name)
            return None

    def add_backup(self, backupset_name):
        """
        Add a new backup to the specified backupset_name, which will also be
        initialized if it does not exist.

        The backup will only exist in memory until its 'flush' method is called
        """
        backupset = self.find_backupset(backupset_name)
        if not backupset:
            backupset = self.add_backupset(backupset_name)
        return backupset.add_backup()

    def find_backupset(self, backupset_name):
        """
        Find an existing backupset.

        If the backupset does not exist None is returned
        """
        path = os.path.join(self.path, backupset_name)
        if not os.path.exists(path):
            return None
        return Backupset(backupset_name, path)

    def add_backupset(self, backupset_name):
        """
        Add a new backupset to this spool.

        If the backupset already exists an IOError is raised
        """
        path = os.path.join(self.path, backupset_name)
        if os.path.exists(path):
            raise IOError("Backupset %s already exists" % backupset_name)
        return Backupset(backupset_name, path)
    
    def list_backupsets(self, name=None, reverse=False):
        """
        Return a list of backupsets under this spool in lexicographical order.

        If reverse is True, the results will be returned in descending lex
        order, ascending otherwise
        """
        if not os.path.exists(self.path):
            return []

        backupsets= []
        dirs = []
        if name:
            if not os.path.exists(os.path.join(self.path, name)):
                return []
            dirs = [name]
        else:
            dirs = [backupset for backupset in os.listdir(self.path) 
                    if os.path.isdir(os.path.join(self.path, backupset))]

        backupsets = [Backupset(dir, os.path.join(self.path, dir)) \
                      for dir in dirs]

        backupsets.sort()

        if reverse:
            backupsets.reverse()

        return backupsets
    
    def list_backups(self, backupset_name=None):
        for backupset in self.list_backupsets(backupset_name):
            for backup in backupset.list_backups():
                yield backup

    def __iter__(self):
        return iter(self.list_backupsets())


class Backupset(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def find_backup(self, name):
        backups = self.list_backups(name)
        if not backups:
            return None
        return backups[0]
    
    def add_backup(self):
        """
        Create a new instance for this job
        """
        backup_name = timestamp_dir()
        backup_path = os.path.join(self.path, backup_name)
        
        return Backup(backup_path, self.name, backup_name)

    def purge(self, retention_count=0):
        if retention_count < 0:
            raise ValueError("Invalid retention count %s" % retention_count)
        for backup in itertools.islice(self.list_backups(reverse=True), retention_count, None):
            backup.purge()
            yield backup

    def list_backups(self, name=None, reverse=False):
        """
        Return list of backups for this backupset in order of their
        creation date.
        """
        if not os.path.exists(self.path):
            return None

        name = (name or "").strip()

        backup_list = []
        if name:
            path = os.path.join(self.path, name)
            return [Backup(path, self.name, name) for x in range(1)
                        if os.path.exists(path)]
        
        dirs = [backup for backup in os.listdir(self.path)
                   if os.path.isdir(os.path.join(self.path, backup))]

        backup_list = [Backup(os.path.join(self.path, dir),
                              self.name,
                              dir) for dir in dirs]

        backup_list.sort()
        if reverse:
            backup_list.reverse()

        return backup_list

    def __iter__(self):
        return iter(self.list_backups())

    def __str__(self):
        return "%s [%s]" % (self.name, self.path)

    def __cmp__(self, other):
        return cmp(self.name, other.name)

CONFIGSPEC = """
[holland:backup]
plugin                  = string(default="")
start-time              = float(default=0)
stop-time               = float(default=0)
failed-backup           = boolean(default=no)
estimated-size          = float(default=0)
on-disk-size            = float(default=0)
estimated-size-factor   = float(default=1.0)
backups-to-keep          = integer(min=0, default=1)
auto-purge-failures     = boolean(default=yes)
purge-policy            = option(manual, before-backup, after-backup, default='after-backup')
""".splitlines()

class Backup(object):
    """
    Representation of a backup instance.
    """
    def __init__(self, path, backupset, name):
        self.path = path
        self.backupset = backupset 
        self.name = '/'.join((backupset, name))
        # Initialize an empty config
        # This will not be loaded until load_config is called
        config_path = os.path.join(self.path, 'backup.conf')
        self.config = BaseConfig({}, file_error=False)
        self.config.filename = config_path
        if os.path.exists(config_path):
            self.load_config()
        else:
            self.validate_config()

    def validate_config(self):
        self.config.validate_config(CONFIGSPEC, suppress_warnings=True)

    def load_config(self):
        """
        (Re)Load the config for this backup.
        """
        self.config.reload()
        self.validate_config()

    def purge(self, data_only=False):
        """
        Purge this backup.
        """
        assert(os.path.realpath(self.path) != '/')
        if data_only:
            # only purge data - preserve metadata
            # FIXME: this would be a more sensical scheme
            if os.path.exists(os.path.join(self.path, 'data')):
                shutil.rmtree(os.path.join(self.path, 'data'))
        else:
            # purge the entire backup directory
            if os.path.exists(self.path):
                shutil.rmtree(self.path)
    
    def exists(self):
        """
        Check if this backup exists on disk
        """
        return os.path.exists(self.path)

    def prepare(self):
        """
        Prepare this backup on disk.  Ensures the path to this backup is created,
        but does not flush any other backup metadata.
        """
        if not self.exists():
            os.makedirs(self.path)
            LOGGER.info("Creating backup path %s", self.path)
        
    def flush(self):
        """
        Flush this backup to disk.  Ensure the path to this backup is created
        and write the backup.conf to the backup directory.
        """
        self.prepare()
        LOGGER.debug("Writing out config to %s", self.config.filename)
        self.config.write()

    def _formatted_config(self):
        from holland.core.util.fmt import format_bytes, format_datetime
        cfg = dict(self.config['holland:backup'])
        cfg['stop-time'] = format_datetime(cfg['stop-time'])
        cfg['start-time'] = format_datetime(cfg['start-time'])
        cfg['estimated-size'] = format_bytes(cfg['estimated-size'])
        cfg['on-disk-size'] = format_bytes(cfg['on-disk-size'])
        return cfg

    def info(self):
        from holland.core.util.template import Template
        from textwrap import dedent, wrap
        tmpl = Template("""
        backup-plugin   = ${plugin}
        backup-started  = ${start-time}
        backup-finished = ${stop-time}
        estimated size  = ${estimated-size}
        on-disk size    = ${on-disk-size}
        """)
        str = tmpl.safe_substitute(self._formatted_config())
        str = "\t" + dedent(str).lstrip()
        str = "\n\t\t".join(str.splitlines())
        return str
        
    def __str__(self):
        from textwrap import dedent
        from holland.core.util.fmt import format_bytes, format_datetime

        return dedent("""
        Backup: %s
        start-time:     %s
        stop-time:      %s
        estimated-size: %s
        on-disk-size:   %s
        """).strip() % (
            self.name,
            format_datetime(self.config.lookup('holland:backup.start-time')),
            format_datetime(self.config.lookup('holland:backup.stop-time')),
            format_bytes(self.config.lookup('holland:backup.estimated-size')),
            format_bytes(self.config.lookup('holland:backup.on-disk-size'))
        ) 
        
    def __cmp__(self, other):
        return (self.config['holland:backup']['start-time'] 
                - other.config['holland:backup']['start-time'])
 
spool = Spool()
