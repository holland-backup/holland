import __builtin__

__all__ = (
    'file', 'open',
    'replace_builtins', 'restore_builtins',
    'original_file', 'original_open'
)

from warnings import warn

original_file = __builtin__.file
original_open = __builtin__.open


# bad for introspection?
DEFAULT = object()

# switch to a regex?
READ_MODES = ('r', 'rb', 'rU')
WRITE_MODES = ('w', 'wb', 'a', 'ab')

MIXED_MODES = ('r+', 'r+b', 'w+', 'w+b', 'a+', 'a+b')
ALL_MODES = READ_MODES + WRITE_MODES + MIXED_MODES
READ_MODES += MIXED_MODES
WRITE_MODES += MIXED_MODES


# would need something a little less basic if os.read
# is implemented...
_fileno_counter = 2
def get_new_fileno():
    global _fileno_counter
    _fileno_counter += 1
    return _fileno_counter


class file(object):
    """file(name[, mode]) -> file object

Open a file.  The mode can be 'r', 'w' or 'a' for reading (default),
writing or appending.  The file will be created if it doesn't exist
when opened for writing or appending; it will be truncated when
opened for writing.  Add a 'b' to the mode for binary files.
Add a '+' to the mode to allow simultaneous reading and writing.
The preferred way to open a file is with the builtin open() function."""

    def mode(self):
        "file mode, one of r(+)(b), w(+)(b) or a(+)(b)"
        return self._mode
    mode = property(mode)

    def name(self):
        "file name"
        return self._name
    name = property(name)

    def closed(self):
        "True if the file is closed"
        return self._closed
    closed = property(closed)

    def encoding(self):
        "file encoding"
        return None
    encoding = property(encoding)

    def errors(self):
        "Unicode error handler"
        return None
    errors = property(errors)

    def newlines(self):
        "end-of-line convention used in this file"
        return None
    newlines = property(newlines)

    _closed = False
    _mode = 'r'
    
    def __init__(self, name, mode='r'):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"
        if not isinstance(name, basestring):
            raise TypeError('File name argument must be str got: %s' %
                             type(name))
        if not isinstance(mode, basestring):
            raise TypeError('File mode argument must be str got: %s' % 
                            type(mode))
            
        self._name = name
        self._mode = mode
        self._position = 0
        self._data = ''
        self._closed = False
        self._binary = mode.endswith('b')
        self._fileno = get_new_fileno()
        self._in_iter = False
        self._softspace = 0
        
        if mode not in ALL_MODES:
            raise ValueError("The only supported modes are r(+)(b), w(+)(b) "
                             "and a(+)(b), not %r" % mode)
        if name == '':
            raise IOError("No such file or directory: ''")
        
        if mode in READ_MODES and mode[0] not in ('a', 'w'):
            self._open_read()
        elif mode in WRITE_MODES:
            if mode.startswith('a'):
                self._open_append()
            else:
                self._open_write()
        else:
            # double check and remove this branch!
            raise AssertionError('whoops - not possible, surely??')
    
    
    def _open_read(self):
        if not backend.CheckForFile(self.name):
            raise IOError('No such file or directory: %r' % self.name)
        data = backend.LoadFile(self.name)
        if not self._binary:
            data = data.replace('\r\n', '\n')
        self._data = data
    
        
    def _open_write(self):
        backend.SaveFile(self.name, '')
        
    
    def _open_append(self):
        if backend.CheckForFile(self.name):
            self._open_read()
            self._position = len(self._data)
        else:
            self._open_write()
    
    
    def _check_int_argument(self, arg):
        if isinstance(arg, float):
            arg = int(arg)
            warn(DeprecationWarning('Integer argument expected got float'))
        elif not isinstance(arg, (int, long)):
            raise TypeError('Integer argument expected. Got %s' % type(arg))
        return arg


    def read(self, size=DEFAULT):
        """read([size]) -> read at most size bytes, returned as a string.

        If the size argument is negative or omitted, read until EOF is reached.
        Notice that when in non-blocking mode, less data than what was requested
        may be returned, even if no size parameter was given."""
        if self.mode not in READ_MODES:
            raise IOError('Bad file descriptor')
        if self.closed:
            raise ValueError('I/O operation on closed file')
        if self._in_iter:
            raise ValueError('Mixing iteration and read methods would '
                             'lose data')
        
        pos = self._position
        if pos == 0 and self.mode not in WRITE_MODES:
            # can't do this when we are in a mixed read / write mode like r+
            # could do this on every read, not just when pos is 0?
            self._open_read()
        
        if size is DEFAULT:
            size = len(self._data)
        else:
            size = self._check_int_argument(size)
            if size < 0:
                size = len(self._data)
        
        data = self._data[pos: pos + size]
        self._position += len(data)
        return data
    
    
    def write(self, data):
        """write(str) -> None.  Write string str to file.

Note that due to buffering, flush() or close() may be needed before
the file on disk reflects the data written."""
        if self.mode not in WRITE_MODES:
            raise IOError('Bad file descriptor')
        if self.closed:
            raise ValueError('I/O operation on closed file')

        self._softspace = 0
        
        if not data:
            return
        if not self._binary:
            data = data.replace('\n', '\r\n')
        
        position = self._position
        start = self._data[:position]
        padding = (position - len(start)) * '\x00'
        end = self._data[position + len(data):]
        self._data = start + padding + data + end
        self._position = position + len(data)
    
        
    def close(self):
        """close() -> None or (perhaps) an integer.  Close the file.

Sets data attribute .closed to True.  A closed file cannot be used for
further I/O operations.  close() may be called more than once without
error.  Some kinds of file objects (for example, opened by popen())
may return an exit status upon closing."""
        if self.closed:
            return
        self._closed = True
        if self.mode in WRITE_MODES:
            backend.SaveFile(self.name, self._data)


    def __repr__(self):
        "x.__repr__() <==> repr(x)"
        state = 'open'
        if self.closed:
            state = 'closed'
        return '<%s file %r mode %r>' % (state, self.name, self.mode)
        
    
    def __del__(self):
        "alias for close()"
        self.close()

        
    def seek(self, position, whence=0):
        """seek(offset[, whence]) -> None.  Move to new file position.

Argument offset is a byte count.  Optional argument whence defaults to
0 (offset from start of file, offset should be >= 0); other values are 1
(move relative to current position, positive or negative), and 2 (move
relative to end of file, usually negative, although many platforms allow
seeking beyond the end of a file).  If the file is opened in text mode,
only offsets returned by tell() are legal.  Use of other offsets causes
undefined behavior.
Note that not all file objects are seekable."""
        position = self._check_int_argument(position)
        whence = self._check_int_argument(whence)
        if not 0 <= whence <= 2:
            raise IOError('Invalid Argument')
        
        if whence == 1:
            position = self._position + position
        elif whence == 2:
            position = len(self._data) + position
            
        if position < 0:
            raise IOError('Invalid Argument')
        self._in_iter = False
        self._position = position

        
    def tell(self):
        "tell() -> current file position, an integer (may be a long integer)."
        return self._position


    def flush(self):
        "flush() -> None.  Flush the internal I/O buffer."
        if self.mode not in WRITE_MODES:
            raise IOError('Bad file descriptor')
        backend.SaveFile(self.name, self._data)


    def isatty(self):
        "isatty() -> true or false.  True if the file is connected to a tty device."
        return False

    
    def fileno(self):
        """fileno() -> integer "file descriptor".

This is needed for lower-level file interfaces, such os.read()."""
        return self._fileno

    
    def __iter__(self):
        "x.__iter__() <==> iter(x)"
        return self

    
    def next(self):
        "x.next() -> the next value, or raise StopIteration"
        if self.mode in WRITE_MODES:
            raise IOError('Bad file descriptor')
        self._in_iter = True
        if self._position >= len(self._data):
            raise StopIteration
        return self.readline()
    
    
    def readline(self, size=DEFAULT):
        """readline([size]) -> next line from the file, as a string.

Retain newline.  A non-negative size argument limits the maximum
number of bytes to return (an incomplete line may be returned then).
Return an empty string at EOF."""
        if self.mode in WRITE_MODES:
            raise IOError('Bad file descriptor')
        
        if size is not DEFAULT:
            size = self._check_int_argument(size)
            if size < 0:
                # treat negative integers the same as DEFAULT
                size = DEFAULT
        
        if self._position >= len(self._data):
            return ''
        
        position = self._position
        remaining = self._data[position:]
        poz = remaining.find('\n')
        
        if poz == -1:
            if size is DEFAULT or size > len(remaining):
                self._position = len(self._data)
                return remaining
            actual = remaining[:size]
            self._position += len(actual)
            return actual
        
        if size is DEFAULT:
            self._position = position + poz + 1
            return remaining[:poz + 1]
        
        actual = remaining[:poz + 1]
        if len(actual) <= size:
            self._position += len(actual)
            return actual
        self._position += size
        return actual[:size]


    def readlines(self, size=DEFAULT):
        """readlines([size]) -> list of strings, each a line from the file.

Call readline() repeatedly and return a list of the lines so read.
The optional size argument, if given, is an approximate bound on the
total number of bytes in the lines returned."""
        if self.mode in WRITE_MODES:
            raise IOError('Bad file descriptor')
        
        # argument actually ignored
        if size is not DEFAULT:
            self._check_int_argument(size)

        result = list(self)
        self._in_iter = False
        return result
    
    
    def xreadlines(self):
        """xreadlines() -> returns self.

For backward compatibility. File objects now include the performance
optimizations previously implemented in the xreadlines module."""
        return self

    
    def _set_softspace(self, value):
        self._softspace = self._check_int_argument(value)
    
    def _get_softspace(self):
        return self._softspace
    
    softspace = property(_get_softspace, _set_softspace, 
                         doc="flag indicating that a space needs to be printed; used by print")
    
    
    def truncate(self, size=DEFAULT):
        """truncate([size]) -> None.  Truncate the file to at most size bytes.

Size defaults to the current file position, as returned by tell()."""
        if self.mode in READ_MODES:
            raise IOError('Bad file descriptor')
        if size is not DEFAULT:
            size = self._check_int_argument(size)
            if size < 0:
                raise IOError('Invalid argument')
        else:
            size = self._position
        data = self._data[:size]
        self._data = data + (size - len(data)) * '\x00'
        self.flush()
        
    
    def writelines(self, sequence):
        """writelines(sequence_of_strings) -> None.  Write the strings to the file.

Note that newlines are not added.  The sequence can be any iterable object
producing strings. This is equivalent to calling write() for each string."""
        if self.mode not in WRITE_MODES:
            raise IOError('Bad file descriptor')
        
        if getattr(sequence, '__iter__', None) is None:
            raise TypeError('writelines() requires an iterable argument')
        
        for line in sequence:
            self.write(line)
    
            
    def __enter__(self):
        "__enter__() -> self."
        return self
    

    def __exit__(self, *excinfo):
        "__exit__(*excinfo) -> None.  Closes the file."
        self.close()

    

def open(name, mode='r', bufsize=None):
    """open(name[, mode]) -> file object

Open a file using the file() type, returns a file object.  This is the
preferred way to open a file."""
    return file(name, mode)

def mkdir(path, mode=None):
    """mkdir(path [, mode=0777])"""

def replace_builtins():
    "replace file and open in the builtin module"
    __builtin__.file =  file
    __builtin__.open = open

def restore_builtins():
    "restore the original file and open to the builtin module"
    __builtin__.file =  original_file
    __builtin__.open = original_open

    
_store = {}

class backend(object):
    "Example backend."
    
    def CheckForFile(filename):
        return filename in _store
    CheckForFile = staticmethod(CheckForFile)

    def DeleteFile(filename):
        del _store[filename]
    DeleteFile = staticmethod(DeleteFile)

    def LoadFile(filename):
        return _store[filename]
    LoadFile = staticmethod(LoadFile)

    def SaveFile(filename, data):
        _store[filename] = data
    SaveFile = staticmethod(SaveFile)
