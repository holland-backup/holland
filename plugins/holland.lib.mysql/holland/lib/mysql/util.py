"""
MySQL related utility functions
"""

import re


def parse_size(units_string):
    """Parse a MySQL-like size string into bytes.

    This function converts a human-readable size string (like '4G' for 4 gigabytes) into
    its equivalent number of bytes. It supports various unit suffixes (K, M, G, T, P, E)
    and their lowercase variants.

    Args:
        units_string (str): A string representing a size with an optional unit suffix.
            Examples: '4G', '1024M', '1.5T'

    Returns:
        int: The number of bytes represented by the input string.

    Raises:
        ValueError: If the input string does not match the expected format.

    Examples:
        >>> parse_size('4G')
        4294967296
        >>> parse_size('1024M')
        1073741824
        >>> parse_size('1.5T')
        1649267441664
    """

    units_string = str(units_string)

    units = "kKmMgGtTpPeE"

    match = re.match(r"^(\d+(?:[.]\d+)?)([%s]?)$" % units, units_string)
    if not match:
        raise ValueError("Invalid constant size syntax %r" % units_string)
    number, unit = match.groups()

    if not unit:
        return int(float(number))

    unit = unit.upper()

    exponent = "KMGTPE".find(unit)

    return int(float(number) * 1024 ** (exponent + 1))
