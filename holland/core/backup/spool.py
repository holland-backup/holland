"""
    holland.core.backup.spool
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides support for managing a spool directory of backups

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

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
    def __init__(self, message, pid):
        SpoolError.__init__(self, message)
        self.message = message
        self.pid = pid


class BackupStore(object):
    """An instance of a Backup directory under a Holland BackupSpool

    :attr name: name of this BackupStore; This is the name of the backupset
                this store is saved under (e.g. 'mysql-lvm')
    :attr path: directory for this BackupStore; This is the absolute
                path to the BackupStore (e.g.
                /var/spool/holland/mysql-lvm/20110101_000000.XXXXX)
    :attr spool: ``BackupSpool`` instance this store is associated with
    """

    def __init__(self, name, path, spool=None):
        self.name = name
        self.path = path
        self.spool = spool
        # cached size of last known size even if we're purged
        self._size = 0
        # to lock this backup to coordinate backup/purging
        self._lock = None

    def latest(self, name=None):
        """Find the latest backup by a backupset name

        This method is used to find the most recent backup for given
        backupset. If ``name`` is not specified, this will search the
        backupset associated wit this ``BackupStore`` instance.

        :returns: ``BackupStore`` instance which may be identical to ``self``
        """
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
        """Find the backup store temporally preceding this one

        This method is used to find the location on disk of the
        last backup made (if one is available)

        :returns: ``BackupStore`` instance if there is a previous backup in the
                  same backupset as this instance, or None if no previous
                  backups are available.
        """
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
        """Calculate the size on disk occupied by this backup store

        :returns: bytes occupied by this backup store
        """
        try:
            self._size = directory_size(self.path)
        except OSError, exc:
            if exc.errno != errno.ENOENT:
                raise
        return self._size

    def spool_capacity(self):
        """Calculate the available space for the underlying storage device
        this BackupStore resides on

        :returns: int number of bytes available
        """
        return disk_free(self.path)

    def check_space(self, required_bytes):
        """Verify that at least ``required_bytes`` of space are available on
        the underlying storage device for this BackupStore

        :raises: SpoolError is unsufficient space is available
        """
        if self.spool_capacity() < required_bytes:
            raise SpoolError("Insufficient space")

    #@property
    def timestamp(self):
        """Timestamp of last modification for the backup store directory"""
        try:
            return os.stat(self.path).st_mtime
        except OSError:
            return 0
    #python2.3 compatibility
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
        """Add a new backup store under this spool

        This creates a new entry under this spool suitable for storing
        data from a backup run. This is stored in a hierchical fashion of::

           $root/
                $backupset/
                          $backup_store/

        Using standard holland paths for a backupset name 'mysqldump' this
        would look like:

        /var/spool/holland/mysqldump/20110101_00000.XXXXX

        Unlike Holland-1.0, tempfile.mkdtemp() is used to generate the backup
        store directory and a random suffix is added.

        :param name: Name of the backupset (e.g. mysql-lvm)
        :param storename: Name of the store directory. If storename is not
                          specified defaults to current timestamp
        :returns: ``BackupStore`` instance
        """
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
        """Load an existing backup store given a full directory path

        :param path: path to the backup store
        :returns: ``BackupStore`` instance
        """
        # check that we're not loading a store that's not a child of this spool
        if os.path.commonprefix([self.root, path]) != self.root:
            raise SpoolError("load_store() requested for %s which is not a "
                             "subdirectory of %s" % (path, self.root))

        name = os.path.basename(os.path.dirname(path))
        return BackupStore(name, path, self)

    def list_backups(self, name):
        """List backups for a backupset in order by time

        :returns: list of ``BackupStore`` instances for the backupset
                  referenced by ``name``
        """
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
        #python2.3 compatibility
        results.sort()
        return results

    def list_backupsets(self):
        """List all backupsets

        :returns: list of strings of backupset names
        """
        results = []
        for name in os.listdir(self.root):
            path = os.path.join(self.root, name)
            if os.path.isdir(path):
                results.append(name)
        #python2.3 compatibility
        results.sort()
        return results

    def lock(self, name):
        """Lock the backupset called ``name`` under this spool

        A lock will be checked prior to performing any critical operation such
        as purging or allocating new backup stores.

        This method flocks a '.holland' file under the ``name`` backupset
        directory under this spool.  (e.g.
        /var/spool/holland/default/.holland).  Such a lock is used to serialize
        access to a single backupset and avoid concurrent purge+backup
        operations from interfering with each other in undefined ways.

        It is the callers responsibility to hold a reference to the open
        .holland lock and close it to release the lock.

        :param name: name of the backupset to lock
        :returns: open file-object associated with this lock
        """
        try:
            os.makedirs(os.path.join(self.root, name))
            LOG.info("Created %s", os.path.join(self.root, name))
        except OSError, exc:
            if exc.errno != errno.EEXIST:
                raise SpoolError("Error when locking spool: %s" % exc)

        try:
            lock = open(os.path.join(self.root, name, '.holland'), 'a+')
            lock.seek(0)
        except IOError, exc:
            LOG.info("%s exits: %s", os.path.join(self.root, name),
                     os.path.exists(os.path.join(self.root, name)))
            raise SpoolError("Could not create lock file %s: %s" %
                             (os.path.join(self.root, name, '.holland'),
                              exc))
        try:
            fcntl.lockf(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except IOError, exc:
            if exc.errno in (errno.EAGAIN, errno.EACCES):
                pid = lock.read()
                raise SpoolLockError("Failed to acquire lock: %s" % exc, pid)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        return lock

    def purge(self, backupset, retention_count=0, dry_run=False):
        """Purge backups in a backupset

        :param backupset: backupset to purge
        :param retention_count: number of backups within the backupset to
                                retain
        :param dry_run: whether to actually run the purge or only return
                        the ``BackupStore`` lists that would be affected
                        (default: False - do a real purge)
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
