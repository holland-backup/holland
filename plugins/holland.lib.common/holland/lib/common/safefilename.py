"""
Convert Database names to safe file names
"""

import string

SAFE_CHARACTERS = string.ascii_letters + string.digits + string.punctuation


def encode(filename):
    """Convert database names  to safe filesystem names.
    """
    output = ""
    for char in filename:
        if char in SAFE_CHARACTERS:
            output += str(char)
        else:
            output += "(" + hex(ord(char))[2:] + ")"
    return output
