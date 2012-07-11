import os
import logging
import errno
import subprocess
import which

LOGGER = logging.getLogger(__name__)

COMPRESSION_METHODS = {
    'gzip'  : ('gzip', '.gz'),
    'pigz'  : ('pigz', '.gz'),
    'bzip2' : ('bzip2', '.bz2'),
    'pbzip2': ('pzip2', '.bz2'),
    'lzop'  : ('lzop', '.lzo'),
    'lzma'  : ('xz', '.xz'),
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
        try:
            return which.which(cmd), ext
        except which.WhichError, e:
            raise OSError("No command found for compression method '%s'" %
                    method)
    except KeyError:
        raise OSError("Unsupported compression method '%s'" % method)

class CompressionInput(object):
    """
    Class to create a compressed file descriptor for reading.  Functions like
    a standard file descriptor such as from open().
    """
    def __init__(self, path, mode, cmd, bufsize=1024*1024):
        self.fileobj = open(path, 'r')
        self.pid = subprocess.Popen([cmd, '--decompress'], 
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

    def next(self):
        return self.pid.stdout.next()

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
    def __init__(self, path, mode, cmd, level, inline):
        self.cmd = cmd
        self.level = level
        self.inline = inline
        if not inline:
            self.fileobj = open(os.path.splitext(path)[0], mode)
            self.fd = self.fileobj.fileno()
        else:
            self.fileobj = open(path, 'w')
            args = [cmd]
            if level:
                args += ['-%d' % level]
            self.pid = subprocess.Popen(args, 
                                        stdin=subprocess.PIPE, 
                                        stdout=self.fileobj.fileno(), 
                                        stderr=subprocess.PIPE)
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
            args = [self.cmd]
            if self.level:
                args += ['-%d' % self.level, '-']
            self.fileobj.close()
            self.fileobj = open(self.fileobj.name, 'r')
            cmp_f = open(self.name, 'w')
            LOGGER.debug("Running %r < %r[%d] > %r[%d]", 
                         args, self.fileobj.name, self.fileobj.fileno(), 
                         cmp_f.name, cmp_f.fileno())
            pid = subprocess.Popen(args, 
                                   stdin=self.fileobj.fileno(), 
                                   stdout=cmp_f.fileno())
            status = pid.wait()
            os.unlink(self.fileobj.name)
        else:
            self.pid.stdin.close()
            # Check for anything on stderr
            for line in self.pid.stderr:
                errmsg = line.strip()
                if not errmsg:
                    # gzip, among others, output a spurious blank line 
                    continue
                LOGGER.error("Compression Error: %s", errmsg)
            self.fileobj.close()
            status = self.pid.wait()
            if status != 0:
                raise IOError(errno.EPIPE,
                              "Compression program %r exited with status %d" %
                                (self.cmd, status))


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

    cmd, ext = lookup_compression(method)

    if not cmd:
        raise IOError("Unknown compression method '%s'" % cmd)

    if not path.endswith(ext):
        path += ext

    return cmd, path

def open_stream(path, mode, method=None, level=None, inline=True):
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
        cmd, path = stream_info(path, method)
        if not cmd:
            raise IOError("Unknown compression method '%s'" % cmd)

        if mode == 'r':
            return CompressionInput(path, mode, cmd=cmd)
        elif mode == 'w':
            return CompressionOutput(path, mode, cmd=cmd, level=level, 
                                     inline=inline)
        else:
            raise IOError("invalid mode: %s" % mode)
