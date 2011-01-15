import errno
from tempfile import TemporaryFile
from subprocess import Popen, PIPE
from holland.core.stream import StreamPlugin, StreamInfo, StreamError, \
                                PluginInfo
from holland.core.stream.base import RealFileLike

class CompressionStreamPlugin(StreamPlugin):
    name = None
    aliases = ()
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
            return WriteCommand(filename, args)
        else:
            raise StreamError("Invalid mode %r" % mode)

    def info(self, filename, mode, level=None, inline=True):
        args = ''.join([
            self.name,
            'r' in mode and '--decompress' or '--stdout',
            ('w' in mode and inline) and ' (inline)' or ''
        ])
        return StreamInfo(
            extension=self.extension,
            name=filename + self.extension,
            description=args
        )


class ReadCommand(RealFileLike):
    def __init__(self, filename, argv):
        self.name = filename
        self._fileobj = open(filename, 'r')
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
        self._fileobj = open(filename, 'w')
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


class LzopPlugin(CompressionStreamPlugin):
    name = 'lzop'
    extension = '.lzo'


class BzipPlugin(CompressionStreamPlugin):
    name = 'bzip2'
    aliases = ['pbzip2']
    extension = '.bz'


class LzmaPlugin(CompressionStreamPlugin):
    name = 'lzma'
    aliases = ['xz', 'pxz']
    extension = '.xz'

    def __init__(self, name):
        if name == 'lzma':
            name = 'xz'
        self.name = name
