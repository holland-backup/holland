# -*- coding: utf-8 -*-
#
#    Copyright © 2007, 2008 Torsten Bronger <bronger@physik.rwth-aachen.de>
#
#    This file is part of the Bobcat program.
#
#    Bobcat is free software; you can use it, redistribute it and/or modify it
#    under the terms of the MIT license.
#
#    You should have received a copy of the MIT license with Bobcat.  If not,
#    see <http://bobcat.origo.ethz.ch/wiki/Licence>.
#

# pylint: skip-file

"""Codec class for safe filenames.  Safe filenames work on all important
filesystems, i.e., they don't contain special or dangerous characters, and
they don't assume that filenames are treated case-sensitively.

    >>> u"hallo".encode("safefilename")
    'hallo'
    >>> u"Hallo".encode("safefilename")
    '{h}allo'
    >>> u"MIT Thesis".encode("safefilename")
    '{mit}_{t}hesis'
    >>> u"Gesch\\u00e4ftsbrief".encode("safefilename")
    '{g}esch(e4)ftsbrief'

Of course, the mapping works in both directions as expected:

    >>> "{g}esch(e4)ftsbrief".decode("safefilename")
    u'Gesch\\xe4ftsbrief'
    >>> "{mit}_{t}hesis".decode("safefilename")
    u'MIT Thesis'

"""
from string import ascii_letters

safe_characters = ascii_letters + "0123456789-_+!$%&'@~#.,^"

def encode(filename, errors='strict'):
    """Convert Unicode strings to safe filenames.

    :Parameters:
      - `filename`: the input string to be converted into a safe filename
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods

    :type filename: unicode
    :type errors: str

    :Return:
      the safe filename

    :rtype: str
    """
    output = ""
    i = 0
    input_length = len(filename)
    while i < input_length:
        char = filename[i]
        if char in safe_characters:
            output += str(char)
        else:
            output += "(" + hex(ord(char))[2:] + ")"
        i += 1
    return output, input_length

def handle_problematic_characters(errors, filename, start, end, message):
    """Trivial helper routine in case something goes wrong in `decode`.

    :Parameters:
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods.  It is just passed by `decode`.
      - `filename`: the input to be converted to Unicode by `decode`
      - `start`: the starting position of the problematic area as an index in
        ``filename``
      - `end`: the ending position of the problematic area as an index in
        ``filename``.  Note that this obeys to the standard upper-limit
        notation in Python (range() etc).
      - `message`: error message describing the problem

    :type errors: str
    :type filename: str
    :type start: int
    :type end: int
    :type message: str

    :Return:
      the single character to be inserted into the output string

    :rtype: unicode
    """
    if errors == 'ignore':
        return ""
    elif errors == 'replace':
        return "?"
    else:
        raise UnicodeDecodeError("safefilename", filename, start, end, message)

def decode(filename, errors='strict'):
    """Convert safe filenames to Unicode strings.

    :Parameters:
      - `filename`: the input string to be converted from a safe filename to an
        ordinary Unicode string
      - `errors`: the ``errors`` parameter known from standard ``str.encode``
        methods

    :type filename: str
    :type errors: str

    :Return:
      the plain Unicode string

    :rtype: unicode
    """
    filename = str(filename)
    input_length = len(filename)
    output = ""
    i = 0
    while i < input_length:
        char = filename[i]
        if char in safe_characters:
            output += char
        elif char == "(":
            end_position = filename.find(")", i)
            if end_position == -1:
                end_position = i+1
                while end_position < input_length and \
                        filename[end_position] in "0123456789abcdef" and \
                        end_position - i <= 8:
                    end_position += 1
                # In you want to implement StreamReaders: If the string
                # didn't start with this curly braces sequence, it should
                # return from here with a smaller value for consumed_length
                output += handle_problematic_characters(errors, filename, i, end_position,
                                                        "open parenthesis was never closed")
                i = end_position
                continue
            else:
                try:
                    output += chr(int(filename[i+1:end_position], 16))
                except:
                    output += handle_problematic_characters(errors, filename, i, end_position+1,
                                                            "invalid data between parentheses")
            i = end_position
        else:
            output += handle_problematic_characters(errors, filename, i, i+1,
                                                    "invalid character '%s'" % char)
        i += 1
    return output, input_length

def registry(encoding):
    """Lookup function for the ``safefilename`` encoding.

    :Parameters:
      - `encoding`: the encoding which is looked for by the caller

    :type encoding: str

    :Return:
      a tuple containing (encoder, decoder, streamencoder, streamdecoder).  The
      latter two are set to ``None`` because they are not implemented (and not
      needed).

    :rtype: tuple
    """
    if encoding == "safefilename":
        return (encode, decode, None, None)
    else:
        return None
