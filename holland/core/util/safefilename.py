"""filename codec for sanitizing random unicode to a known good filename

Based on the identically named codec from the bobcat project
"""

from holland.core.util.pycompat import Scanner

def decode(filename):
    """Decode a filename to the original filename"""
    scanner = Scanner([
        ("[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: t.decode('ascii')),
        ("_", lambda s, t: ' '),
        ('\{[a-z]+\}', lambda s, t: t[1:-1].upper().decode('ascii')),
        ('\([0-9a-f]{1,8}\)', lambda s, t: chr(int(t[1:-1], 16))),
    ])

    filename, remaining = scanner.scan(filename)

    if remaining:
        raise ValueError("Failed to decode %s" % filename)

    return ''.join(filename), len(remaining)

def encode(filename):
    """Encode the unicode string into a filename"""
    scanner = Scanner([
        (r"[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: t.encode('ascii')),
        (r" ", lambda s, t: '_'.encode('ascii')),
        (r'[A-Z]+', lambda s, t: ('{%s}' % t.lower()).encode('ascii')),
        (r'[^a-z0-9-+!$%&\'@~#.,^ A-Z]',
         lambda s, t: ('(%s)' % hex(ord(t))[2:]).encode('ascii')),
    ])

    filename, remaining = scanner.scan(filename)

    if remaining:
        raise ValueError("Failed to decode %s" % filename)

    return ''.encode('ascii').join(filename), len(remaining)
