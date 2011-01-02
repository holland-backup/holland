"""Manage a spool directory"""

import os
import time
import shutil

class SpoolManager(object):
    """Manage a directory spool"""
    def __init__(self, path, format='%Y%m%d_%H%M%S'):
        self.path = path
        self.format = format

    def _format(self):
        """Format an entry name"""
        return time.strftime(self.format)

    def add(self, name):
        """Add a new entry to the backupset under spool"""
        backupset_path = os.path.join(self.path, name)
        job_path = os.path.join(backupset_path, self._format())
        try:
            os.makedirs(job_path)
        except OSError, exc:
            raise

        return SpoolEntry(job_path)

    def remove(self, name):
        """Remove an entire backupset from the spool"""
        for entry in self.list_backups(name):
            entry.remove()

    def list_backupsets(self):
        results = []
        for entry in os.listdir(self.path):
            entry_path = os.path.join(self.path, entry)
            if os.path.isdir(entry_path):
                results.append(entry_path)
        return results

    def list_backups(self, backupset):
        backupset_path = os.path.join(self.path, backupset)
        for entry in os.listdir(backupset_path):
            entry_path = os.path.join(backupset_path, entry)
            yield SpoolEntry(entry_path)

class SpoolEntry(object):
    def __init__(self, path):
        self.path = path

    def remove(self):
        shutil.rmtree(self.path)

    def size(self):
        """Amount of disk space this entry is presently consuming"""
        return 0

    #XXX: ConfigObj does not necessarily create sane ini files so this
    #     could easily fail.  But I hate the dependence on ConfigObj here :(
    def _load_config(self):
        from ConfigParser import RawConfigParser, Error
        config_path = os.path.join(self.path, 'backup.conf')
        cfg = RawConfigParser()
        try:
            cfg.read([config_path])
        except Error:
            pass
        return cfg

    #XXX: @cached_property
    def timestamp(self):
        from ConfigParser import Error
        config = self._load_config()

        try:
            return config.getint('holland:backup', 'start-time')
        except (Error, ValueError):
            return 0
    timestamp = property(timestamp)

    def __cmp__(self, other):
        """Compare to another spoolentry"""
        return cmp(self.timestamp, other.timestamp)

    def __eq__(self, other):
        return other.path == self.path
