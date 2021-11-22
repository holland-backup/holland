"""
Helpful functions
"""

from string import Template


def parse_arguments(arguments, **kwargs):
    """Replace varibles with values"""
    if not arguments:
        return arguments
    if isinstance(arguments, list):
        arguments = " ".join(arguments)
    ret = Template(arguments).safe_substitute(**kwargs)
    ret = ret.split(" ")
    return ret
