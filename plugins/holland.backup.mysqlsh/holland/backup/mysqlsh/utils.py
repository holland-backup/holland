"""
Utility functions for the mysqlsh backup plugin.
"""


def parse_version(version_str):
    """Parse a version string into a tuple of integers."""
    return tuple(map(int, version_str.split(".")))


def kebab_to_camel(kebab_str):
    """Convert kebab-case string to camelCase"""
    words = kebab_str.split("-")
    return words[0] + "".join(word.capitalize() for word in words[1:])
