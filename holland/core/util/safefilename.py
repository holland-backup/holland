"""filename codec for sanitizing random unicode to a known good filename

Based on the identically named codec from the bobcat project
"""

try:
    bytes
except NameError:
    bytes = str

from holland.core.util.pycompat import Scanner

def decode(filename):
    """Decode a filename to the original filename"""
    scanner = Scanner([
        (b"[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: bytes(t).decode('ascii')),
        (b"_", lambda s, t: ' '),
        (b'\{[a-z]+\}', lambda s, t: bytes(t[1:-1]).upper().decode('ascii')),
        (b'\([0-9a-f]{1,8}\)', lambda s, t: chr(int(bytes(t[1:-1]), 16))),
    ])

    data, remaining = scanner.scan(data)

    if remaining:
        raise ValueError("Failed to decode %s" % data)

    return ''.join(data), len(remaining)

def encode(filename):
    """Encode the unicode string into a filename"""
    scanner = Scanner([
        (r"[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: t.encode('ascii')),
        (r" ", lambda s, t: '_'.encode('ascii')),
        (r'[A-Z]+', lambda s, t: ('{%s}' % t.lower()).encode('ascii')),
        (r'[^a-z0-9-+!$%&\'@~#.,^ A-Z]',
         lambda s, t: ('(%s)' % hex(ord(t))[2:]).encode('ascii')),
    ])

    data, remaining = scanner.scan(data)

    if remaining:
        raise ValueError("Failed to decode %s" % data)

    return ''.encode('ascii').join(data), len(remaining)
