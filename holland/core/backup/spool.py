"""Management of a directory of backups"""

import os
import time
import errno
import fcntl
import shutil
import tempfile
import logging
from holland.core.util import disk_free, directory_size

LOG = logging.getLogger(__name__)

class SpoolError(Exception):
    """Base error class that all spool errors derive from"""

class SpoolLockError(SpoolError):
    """Raised when a lock error is encountered during a spool operation"""

class BackupStore(object):
    """Manage the storage space of a backup"""
    def __init__(self, name, path, spool=None):
        self.name = name
        self.path = path
        self.spool = spool
        # cached size of last known size even if we're purged
        self._size = 0
        # to lock this backup to coordinate backup/purging
        self._lock = None

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
        self.size() # to cache the size prior to deletion
        shutil.rmtree(self.path)

    def size(self):
        """Find the size on disk occupied by this backup store

        :returns: bytes occupied by this backup store
        """
        try:
            self._size = directory_size(self.path)
        except OSError, exc:
            if exc.errno != errno.ENOENT:
                raise
        return self._size

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
            backup_path = os.path.realpath(backup_path)
            store = BackupStore(name, backup_path, self)
            if store not in results:
                results.append(store)
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

    def lock(self, name):
        """Lock a backupset

        A lock will be checked prior to performing any critical operation such
        as purging or allocating new backup sets.
        """
        try:
            os.mkdir(os.path.join(self.root, name))
        except OSError, exc:
            if exc.errno != errno.EEXIST:
                raise SpoolError("Error when locking spool: %s" % exc)

        lock = open(os.path.join(self.root, name, '.holland'), 'a')
        try:
            fcntl.lockf(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except IOError, exc:
            if exc.errno in (errno.EAGAIN, errno.EACCES):
                raise SpoolLockError("Failed to acquire lock: %s" % exc)
        return lock

    def purge(self, backupset, retention_count=0, dry_run=False):
        """Purge backups in a backupset

        :returns: tuple of backup sublists
                  (all_backups, sublist_kept, sublist_purged)
        """
        if retention_count < 0:
            raise ValueError("retention_count must not be negative")
        backups = self.list_backups(backupset)
        idx = max(len(backups) - retention_count, 0)
        retained_backups = backups[idx:]
        purged_backups = backups[0:idx]
        if dry_run is False:
            for backup in purged_backups:
                backup.purge()
        return backups, retained_backups, purged_backups

    def __iter__(self):
        for name in self.list_backupsets():
            for store in self.list_backups(name):
                yield store

    def __str__(self):
        return 'BackupSpool(root=%r)' % (self.root)

    __repr__ = __str__
