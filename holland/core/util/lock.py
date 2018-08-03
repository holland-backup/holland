"""A simple fcntl/flock implementation"""

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

        if self.is_locked():
            return

        try:
            self.lock = open(self.path, 'r')
            flock(self.lock, LOCK_EX|LOCK_NB)
        except IOError as exc:
            self.lock = None
            raise LockError(str(exc), exc)
        else:
            return True

    def is_locked(self):
        """Check for lock"""
        return self.lock is not None

    def release(self):
        """Release a currently open lock"""
        if self.lock is None:
            raise LockError("No lock acquired to release")
        try:
            self.acquire()
            flock(self.lock, LOCK_UN)
            self.lock = None
        except IOError as exc:
            raise LockError(str(exc), exc)
        else:
            return True
