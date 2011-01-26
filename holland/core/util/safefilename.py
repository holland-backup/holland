"""filename codec for sanitizing random unicode to a known good filename

Based on the identically named codec from the bobcat project
"""

import codecs
try:
    bytes
except NameError:
    bytes = str

from holland.core.util.pycompat import Scanner

def decode(input, errors='strict'):
    """Decode a filename into the original unicode string"""
    scanner = Scanner([
        (b"[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: bytes(t).decode('ascii')),
        (b"_", lambda s, t: ' '),
        (b'\{[a-z]+\}', lambda s, t: bytes(t[1:-1]).upper().decode('ascii')),
        (b'\([0-9a-f]{1,8}\)', lambda s, t: chr(int(bytes(t[1:-1]), 16))),
    ])

    data, remaining = scanner.scan(input)

    # XXX: error if len(remaining) > 0

    return ''.join(data), len(remaining)

def encode(input, errors='strict'):
    """Encode the unicode string into a filename"""
    scanner = re.Scanner([
        (r"[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: t.encode('ascii')),
        (r" ", lambda s, t: '_'.encode('ascii')),
        (r'[A-Z]+', lambda s, t: ('{%s}' % t.lower()).encode('ascii')),
        (r'[^a-z0-9-+!$%&\'@~#.,^ A-Z]',
         lambda s, t: ('(%s)' % hex(ord(t))[2:]).encode('ascii')),
    ])

    data, remaining = scanner.scan(input)

    # XXX: error if len(remaining) > 0

    return ''.encode('ascii').join(data), len(remaining)

class Codec(codecs.Codec):
    """Codec class for safefilename"""
    encode = staticmethod(encode)

    decode = staticmethod(decode)

class IncrementalEncoder(codecs.IncrementalEncoder):
    """IncrementEncoder"""
    def encode(self, input, final=False):
        return encode(input, self.errors)[0]

class IncrementalDecoder(codecs.IncrementalDecoder):
    """IncrementalDecoder"""
    def decode(self, input, final=False):
        return encode(input, self.errors)[0]

class StreamWriter(Codec, codecs.StreamWriter):
    """StreamWriter"""
    pass

class StreamReader(Codec, codecs.StreamReader):
    """StreamReader"""
    pass

### encodings module API

def getregentry():
    """codec info used to register the safefilename codec with python"""
    return codecs.CodecInfo(
        name='safefilename',
        encode=Codec.encode,
        decode=Codec.decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )

def search_function(encoding):
    """safefilename codec registration function"""
    if encoding == 'safefilename':
        return getregentry()
codecs.register(search_function)
