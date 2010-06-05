"""A simple fcntl/flock implementation"""

from os import getpid
from fcntl import flock, LOCK_EX, LOCK_UN, LOCK_NB

class LockError(Exception):
    """Raised when an error is encountered during a lock operation"""

    def __init__(self, message, exc=None):
        Exception.__init__(self, message, exc)
        self.message = message
        self.exc = exc

class Lock(object):
    """A simple flock based file lock implementation"""

    def __init__(self, path):
        self.path = path
        self.lock = None

    def acquire(self):
        """Acquire a lock on the path associated with this lock object"""
        try:
            self.lock = open(self.path, 'a')
            flock(self.lock, LOCK_EX|LOCK_NB)
            self.lock.truncate()
            self.lock.write(str(getpid()))
        except IOError, exc:
            self.lock = None
            raise LockError(str(exc), exc)
        else:
            return True

    def release(self):
        """Release a currently open lock"""
        if self.lock is None:
            raise LockError("No lock acquired to release")
        try:
            self.acquire()
            self.lock.truncate()
            flock(self.lock, LOCK_UN)
        except IOError, exc:
            raise LockError(str(exc), exc)
        else:
            return True
