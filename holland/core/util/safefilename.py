"""
    holland.core.util.safefilename
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Encoding/Decoding methods for encoding a string into a safe filename.
    This is useful when a string may contain characters that are not safe for
    for a normal filename as they may contain ``os.sep`` ('/') or various
    unicode characters

    This code was adapted from the encoding of the same name from the bobcat
    project:
        `<http://bobcat.origo.ethz.ch/>_`

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from holland.core.util.pycompat import Scanner

def decode(filename):
    """Decode a ``safefilename`` encoded filename to the original filename

    :returns: original string
    """
    scanner = Scanner([
        ("[a-z0-9-+!$%&\'@~#.,^]+", lambda s, t: t.decode('ascii')),
        ("_", lambda s, t: ' '),
        ('\{[a-z]+\}', lambda s, t: t[1:-1].upper().decode('ascii')),
        ('\([0-9a-f]{1,8}\)', lambda s, t: chr(int(t[1:-1], 16))),
    ])

    filename, remaining = scanner.scan(filename)

    if remaining:
        raise ValueError("Failed to decode %s" % filename)

    return ''.join(filename)

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

    return ''.encode('ascii').join(filename)
