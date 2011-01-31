"""Compression plugins for the holland.core.stream API"""

import os
import errno
from tempfile import TemporaryFile, mkstemp
from subprocess import Popen, PIPE, STDOUT, check_call, CalledProcessError
from holland.core.stream import StreamPlugin, StreamError
from holland.core.stream.base import RealFileLike

class CompressionStreamPlugin(StreamPlugin):
    name = None
    aliases = ()
    summary = ''
    extension = ''

    def open(self, filename, mode, level=None, inline=True):
        if 'r' in mode:
            return ReadCommand(filename, [self.name, '--decompress'])
        elif 'w' in mode:
            if not filename.endswith(self.extension):
                filename += self.extension
            args = [self.name, '--stdout']
            if level:
                args += ['-%d' % abs(level)]
            if inline:
                return WriteCommand(filename, args)
            else:
                return PostCompressFile(args, filename, 'wb')
        else:
            raise StreamError("Invalid mode %r" % mode)

    def stream_info(self, filename, mode, level=None, inline=True):
        args = ''.join([
            self.name,
            'r' in mode and '--decompress' or '--stdout',
            ('w' in mode and inline) and ' (inline)' or ''
        ])
        return dict(
            extension=self.extension,
            name=filename + self.extension,
            description=args
        )

    #@classmethod
    def plugin_info(cls):
        return dict(
            name=cls.name,
            summary=cls.summary,
            author='Rackspace',
            version='1.1.0',
            api_version='1.1.0',
        )
    plugin_info = classmethod(plugin_info)


class PostCompressFile(file):
    def __init__(self, argv, *args, **kwargs):
        self.argv = argv
        file.__init__(self, *args, **kwargs)

    def close(self):
        file.close(self)
        try:
            stdout, tmppath = mkstemp(dir=os.path.dirname(self.name))
            stderr = TemporaryFile()
            check_call(self.argv,
                       stdin=open(self.name, 'r'),
                       stdout=stdout,
                       stderr=stderr,
                       close_fds=True)
            os.rename(tmppath, self.name)
        except CalledProcessError, exc:
            raise IOError("Compression command failed when closing file: %s" %
                          exc)


class ReadCommand(RealFileLike):
    def __init__(self, filename, argv):
        self.name = filename
        self._fileobj = open(filename, 'rb')
        self._err = TemporaryFile()
        self.process = Popen(
            list(argv),
            stdin=self._fileobj,
            stdout=PIPE,
            stderr=self._err,
            close_fds=True
        )

    def close(self):
        if self.closed:
            return
        self.process.stdout.close()
        self.process.wait()
        self.fileobj.close()
        if self.process.returncode != 0:
            raise IOError("gzip exited with non-zero status (%d)" %
                          self.process.returncode)
        RealFileLike.close(self)

    def fileno(self):
        return self.process.stdout.fileno()

    def read(self, size=None):
        args = []
        if size is not None:
            args.append(size)
        return self.process.stdout.read(*args)

    def readline(self, size=None):
        args = []
        if size is not None:
            args.append(size)
        return self.process.stdout.readline(*args)

    def write(self, data):
        raise IOError("File not open for writing")


class WriteCommand(RealFileLike):
    def __init__(self, filename, argv):
        self.name = filename
        self._fileobj = open(filename, 'wb')
        self._err = TemporaryFile()
        try:
            self.process = Popen(
                list(argv),
                stdin=PIPE,
                stdout=self._fileobj,
                stderr=self._err,
                close_fds=True
            )
        except OSError, exc:
            if exc.errno == errno.ENOENT:
                raise IOError("%r: command not found" % argv[0])
            raise

    def close(self):
        if self.closed:
            return
        self.process.stdin.close()
        self.process.wait()
        self._fileobj.close()
        if self.process.returncode != 0:
            raise IOError("gzip exited with non-zero status (%d)" %
                          self.process.returncode)
        RealFileLike.close(self)

    def fileno(self):
        return self.process.stdin.fileno()

    def read(self, size=None):
        raise IOError("File not open for reading")

    def readline(self, size=None):
        self.read()

    def write(self, data):
        self.process.stdin.write(data)

    def writelines(self, sequence):
        self.process.stdin.writelines(sequence)


class GzipPlugin(CompressionStreamPlugin):
    name = 'gzip'
    aliases = ['pigz']
    extension = '.gz'
    summary = 'gzip/pigz compression codec'

class LzopPlugin(CompressionStreamPlugin):
    name = 'lzop'
    extension = '.lzo'
    summary = 'lzop compression codec'

class BzipPlugin(CompressionStreamPlugin):
    name = 'bzip2'
    aliases = ['pbzip2']
    extension = '.bz'
    summary = 'bzip2/pbzip2 compression codec'

class LzmaPlugin(CompressionStreamPlugin):
    name = 'lzma'
    aliases = ['xz', 'pxz']
    extension = '.xz'
    summary = 'lzma compression codec'

    def __init__(self, name):
        if name == 'lzma':
            name = 'xz'
        self.name = name
