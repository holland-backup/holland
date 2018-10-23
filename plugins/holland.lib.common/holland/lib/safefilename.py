"""
Convert Database names to safe file names
"""

import string

safe_characters = string.ascii_letters + string.digits + string.punctuation

def encode(filename):
    """Convert database names  to safe filesystem names.
    """
    output = ""
    for char in filename:
        if char in safe_characters:
            output += str(char)
        else:
            output += "(" + hex(ord(char))[2:] + ")"
    return output
