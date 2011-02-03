"""Management of a directory of backups"""

import os
import time
import errno
import shutil
import tempfile
import logging
from holland.core.util import disk_free

LOG = logging.getLogger(__name__)

class SpoolError(Exception):
    """Base error class that all spool errors derive from"""

class BackupStore(object):
    """Manage the storage space of a backup"""
    def __init__(self, name, path, spool=None):
        self.name = name
        self.path = path
        self.spool = spool

    def latest(self, name=None):
        """Find the latest backup by a backupset name"""
        if not self.spool:
            return None
        if name is None:
            name = self.name
        backups = self.spool.list_backups(name)
        try:
            return backups[-1]
        except IndexError:
            return None

    def oldest(self, count=1):
        """Return the oldest backups in this store's backupset"""
        if not self.spool:
            return []
        backups = self.spool.list_backups(self.name)
        return backups[0:-count]

    def previous(self):
        """Find the backup store temporally preceding this one"""
        if not self.spool:
            return None
        backups = self.spool.list_backups(self.name)
        try:
            index = backups.index(self)
            return backups[index - 1:index][0]
        except IndexError:
            return None

    def purge(self):
        """Purge the data for this backup store"""
        shutil.rmtree(self.path)

    def spool_capacity(self):
        """Find the available space in bytes on this store"""
        return disk_free(self.path)

    def check_space(self, required_bytes):
        """Check that sufficient space exists for this
        backupstore
        """
        if self.spool_capacity() < required_bytes:
            raise SpoolError("Insufficient space")

    #@property
    def timestamp(self):
        """Timestamp of the backup store"""
        try:
            return os.stat(self.path).st_mtime
        except OSError:
            return 0
    #XXX: python2.3 compatibility
    timestamp = property(timestamp)

    def __eq__(self, other):
        return self.path == other.path

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __str__(self):
        return 'BackupStore(name=%r, path=%r, spool=%r)' % \
                    (self.name, self.path, self.spool)

    __repr__ = __str__

class BackupSpool(object):
    """Manage a hierarchical directory of backups

    This spool manages a directory of directories.

    The first level under ``root`` is the backupsets
    Under backupsets are ``BackupStore`` paths that contain
    actual backup data.
    """
    def __init__(self, root):
        self.root = os.path.abspath(root)

    def add_store(self, name, storename=None):
        """Add a new backup store under this spool"""
        if storename is None:
            storename = '%s' % time.strftime('%Y%m%d_%H%M%S')

        try:
            os.makedirs(os.path.join(self.root, name))
        except OSError, exc:
            if exc.errno != errno.EEXIST:
                raise

        backupstore_path = tempfile.mkdtemp(prefix=storename + '.',
                                            dir=os.path.join(self.root, name))
        return BackupStore(name, backupstore_path, self)

    def load_store(self, path):
        """Load an existing backup store"""
        # just check we're not loading a store that's not a child of this spool
        if os.path.commonprefix([self.root, path]) != self.root:
            raise SpoolError("load_store() requested for %s which is not a "
                             "subdirectory of %s" % (path, self.root))

        #XXX: check this is a backupset
        name = os.path.basename(os.path.dirname(path))
        return BackupStore(name, path, self)

    def list_backups(self, name):
        """List backups for a backupset in temporal order"""
        path = os.path.join(self.root, name)
        results = []
        for store_path in os.listdir(path):
            backup_path = os.path.join(path, store_path)
            if not os.path.isdir(backup_path):
                continue
            results.append(BackupStore(name, backup_path, self))
        #XXX: python2.3 compatibility
        results.sort()
        return results

    def list_backupsets(self):
        """List all backupsets"""
        results = []
        for name in os.listdir(self.root):
            path = os.path.join(self.root, name)
            if os.path.isdir(path):
                results.append(name)
        #XXX: python2.3 compatibility
        results.sort()
        return results

    def purge_backupset(self, name, retention_count=0):
        """Purge backups in a backupset"""
        backups = self.list_backups(name)
        while retention_count > 0:
            try:
                backups.pop(-1)
                retention_count -= 1
            except IndexError:
                break
        for backup in backups:
            backup.purge()

    def __iter__(self):
        for name in self.list_backupsets():
            for store in self.list_backups(name):
                yield store

    def __str__(self):
        return 'BackupSpool(root=%r)' % (self.root)

    __repr__ = __str__
