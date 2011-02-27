"""Generic support for loading file-like objects"""

import os
import logging
try:
    SEEK_SET = os.SEEK_SET
    SEEK_CUR = os.SEEK_CUR
    SEEK_END = os.SEEK_END
except AttributeError: #pragma: no cover
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2

LOG = logging.getLogger(__name__)

class FileLike(object):
    """A file-like object"""

    closed = False
    encoding = None
    mode = 'r'
    name = '<unknown>'
    newlines = None
    softspace = 0

    def close(self):
        """Close the file."""
        self.closed = True

    def flush(self):
        """Flush the internal buffer"""

    def next(self):
        """The next line in the file"""
        line = self.readline()
        if not line:
            raise StopIteration()
        return line

    def read(self, size=None):
        """Read at most size bytes from the file"""
        raise NotImplementedError()

    def readline(self, size=None):
        """Read one entire line from the file."""
        raise NotImplementedError()

    def readlines(self, sizehint=None):
        """Read until EOF using readline() and return a list containing the
        lines thus read."""
        raise NotImplementedError()

    def seek(self, offset, whence=SEEK_SET):
        """Set the file's current position"""

    def tell(self):
        """Return the file's current position"""
        raise NotImplementedError()

    def truncate(self, size=None):
        """Truncate the file's size"""

    def write(self, data):
        """Write a string to the file"""

    def writelines(self, sequence):
        """Write a sequence of strings to the file"""

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        LOG.debug("__exit__(exc_type=%r, exc_val=%r, exc_tb=%r)",
                  exc_type, exc_val, exc_tb)
        self.close()
        return False

class RealFileLike(FileLike):
    """FileLike objects backed by a real file descriptor"""

    def fileno(self):
        """Return the integer "file descriptor" that is used by the underlying
        implementation to request I/O operations from the operating system"""
        return -1

    def tell(self):
        """Return the file's current position"""
        return os.lseek(self.fileno(), SEEK_CUR)

    def isatty(self):
        """Return True if the file is connected to a tty(-like) device, else
        False"""
        return os.isatty(self.fileno())

class PlainFile(RealFileLike, file):
    """Wrapper for a real file object"""

    def fileno(self):
        """Return the integer "file descriptor" that is used by the underlying
        implementation to request I/O operations from the operating system"""
        return self.fileno()
