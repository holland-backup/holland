import os
import logging
import errno
import subprocess
from . import which
import shlex
from tempfile import TemporaryFile

LOG = logging.getLogger(__name__)

#: This is a simple table of method_name : (command, extension)
#: mappings.
COMPRESSION_METHODS = {
    'gzip'  : ('gzip', '.gz'),
    'gzip-rsyncable' : ('gzip --rsyncable', '.gz'),
    'pigz'  : ('pigz', '.gz'),
    'bzip2' : ('bzip2', '.bz2'),
    'pbzip2': ('pbzip2', '.bz2'),
    'lzop'  : ('lzop', '.lzo'),
    'lzma'  : ('xz', '.xz'),
    'gpg'   : ('gpg -e --batch --no-tty', '.gpg'),
}

def lookup_compression(method):
    """
    Looks up the passed compression method in supported COMPRESSION_METHODS
    and returns a tuple in the form of ('command_name', 'file_extension').

    Arguments:

    method -- A string identifier of the compression method (i.e. 'gzip').
    """
    try:
        cmd, ext = COMPRESSION_METHODS[method]
        argv = shlex.split(cmd)
        try:
            return [which.which(argv[0])] + argv[1:], ext
        except which.WhichError as e:
            raise OSError("No command found for compression method '%s'" %
                    method)
    except KeyError:
        raise OSError("Unsupported compression method '%s'" % method)

class CompressionInput(object):
    """
    Class to create a compressed file descriptor for reading.  Functions like
    a standard file descriptor such as from open().
    """
    def __init__(self, path, mode, argv, bufsize=1024*1024):
        self.fileobj = open(path, 'r')
        self.pid = subprocess.Popen(argv + ['--decompress'],
                                    stdin=self.fileobj.fileno(),
                                    stdout=subprocess.PIPE,
                                    bufsize=bufsize)
        self.fd = self.pid.stdout.fileno()
        self.name = path
        self.closed = False

    def fileno(self):
        return self.fd

    def read(self, size):
        return os.read(self.fd, size)

    def __next__(self):
        return next(self.pid.stdout)

    def __iter__(self):
        return iter(self.pid.stdout)

    def close(self):
        import signal
        os.kill(self.pid.pid, signal.SIGTERM)
        self.fileobj.close()
        self.pid.stdout.close()
        self.pid.wait()
        self.closed = True


class CompressionOutput(object):
    """
    Class to create a compressed file descriptor for writing.  Functions like
    a standard file descriptor such as from open().
    """
    def __init__(self, path, mode, argv, level, inline):
        self.argv = argv
        self.level = level
        self.inline = inline
        if not inline:
            self.fileobj = open(os.path.splitext(path)[0], mode)
            self.fd = self.fileobj.fileno()
        else:
            self.fileobj = open(path, 'w')
            if level:
                if "gpg" in argv[0]:
                    argv += ['-z%d' % level]
                else:
                    argv += ['-%d' % level]
            LOG.debug("* Executing: %s", subprocess.list2cmdline(argv))
            self.stderr = TemporaryFile()
            self.pid = subprocess.Popen(argv,
                                        stdin=subprocess.PIPE,
                                        stdout=self.fileobj.fileno(),
                                        stderr=self.stderr)
            self.fd = self.pid.stdin.fileno()
        self.name = path
        self.closed = False

    def fileno(self):
        return self.fd

    def write(self, data):
        return os.write(self.fd, data)

    def close(self):
        self.closed = True
        if not self.inline:
            argv = list(self.argv)
            if self.level:
                if "gpg" in argv[0]:
                    argv += ['-z%d' % self.level, '-']
                else:
                    argv += ['-%d' % self.level, '-']
            self.fileobj.close()
            self.fileobj = open(self.fileobj.name, 'r')
            cmp_f = open(self.name, 'w')
            LOG.debug("Running %r < %r[%d] > %r[%d]",
                         argv, self.fileobj.name, self.fileobj.fileno(),
                         cmp_f.name, cmp_f.fileno())
            pid = subprocess.Popen(args,
                                   stdin=self.fileobj.fileno(),
                                   stdout=cmp_f.fileno())
            status = pid.wait()
            os.unlink(self.fileobj.name)
        else:
            self.pid.stdin.close()
            status = self.pid.wait()
            stderr = self.stderr
            stderr.flush()
            stderr.seek(0)
            try:
                if status != 0:
                    for line in stderr:
                        if not line.strip(): continue
                        LOG.error("%s: %s", self.argv[0], line.rstrip())
                    raise IOError(errno.EPIPE,
                              "Compression program '%s' exited with status %d" %
                                (self.argv[0], status))
                else:
                    for line in stderr:
                        if not line.strip(): continue
                        LOG.info("%s: %s", self.argv[0], line.rstrip())
            finally:
                stderr.close()


def stream_info(path, method=None, level=None):
    """
    Determine compression command, and compressed path based on original path
    and compression method.  If method is not passed, or level is 0 the
    original path is returned.

    Arguments:

    path    -- Path to file to compress/decompress
    method  -- Compression method (i.e. 'gzip', 'bzip2', 'pbzip2', 'lzop')
    level   -- Compression level (0-9)
    """
    if not method or level == 0:
        return path

    argv, ext = lookup_compression(method)

    if not argv:
        raise IOError("Unknown compression method '%s'" % argv[0])

    if not path.endswith(ext):
        path += ext

    return argv, path

def _parse_args(value):
    """Convert a cmdline string to a list"""
    if isinstance(value, str):
        value = value.encode('utf8')
    return shlex.split(value)

def open_stream(path,
                mode,
                method=None,
                level=None,
                inline=True,
                extra_args=None):
    """
    Opens a compressed data stream, and returns a file descriptor type object
    that acts much like os.open() does.  If no method is passed, or the 
    compression level is 0, simply returns a file descriptor from open().

    Arguments:

    mode    -- File access mode (i.e. 'r' or 'w')
    method  -- Compression method (i.e. 'gzip', 'bzip2', 'pbzip2', 'lzop')
    level   -- Compression level
    inline  -- Boolean whether to compress inline, or after the file is written.
    """
    if not method or method == 'none' or level == 0:
        return open(path, mode)
    else:
        argv, path = stream_info(path, method)
        if extra_args:
            argv += _parse_args(extra_args)
        if mode == 'r':
            return CompressionInput(path, mode, argv=argv)
        elif mode == 'w':
            return CompressionOutput(path, mode, argv=argv, level=level,
                                     inline=inline)
        else:
            raise IOError("invalid mode: %s" % mode)
