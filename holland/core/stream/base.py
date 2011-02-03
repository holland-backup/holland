"""Generic support for loading file-like objects"""

import os
try:
    SEEK_SET = os.SEEK_SET
    SEEK_CUR = os.SEEK_CUR
    SEEK_END = os.SEEK_END
except AttributeError: #pragma: no cover
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2

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
        return ''

    def readline(self, size=None):
        """Read one entire line from the file."""
        return ''

    def readlines(self, sizehint=None):
        """Read until EOF using readline() and return a list containing the
        lines thus read."""
        return [line for line in self]

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
        self.close()
        return False

class RealFileLike(FileLike):
    """FileLike objects backed by a real file descriptor"""

    def fileno(self):
        """Return the integer "file descriptor" that is used by the underlying
        implementation to request I/O operations from the operating system"""
        raise NotImplementedError()

    def tell(self):
        return os.seek(self.fileno(), SEEK_CUR)

    def isatty(self):
        """Return True if the file is connected to a tty(-like) device, else
        False"""
        return os.isatty(self.fileno())

class PlainFile(RealFileLike, file):
    """Wrapper for a real file object"""
