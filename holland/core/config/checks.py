"""
Extra check methods to work with
a validate.py Validator instance
"""

import shlex
from builtins import str as text
from holland.core.util.fmt import format_loglevel
try:
    from configobj.validate import Validator
except ImportError:
    from . import validate as validate
    from .validate import Validator

def is_coerced_list(value, min_val=None, max_val=None):
    """
    Checks if a value is a list, if not coerces
    it to a list
    """
    if isinstance(value, text):
        value = [value]
    return validate.is_list(value, min_val, max_val)

def is_octal(value, min_val=None, max_val=None):
    """
    Coerces a value to octal
    """
    if not isinstance(value, text):
        return validate.is_integer(value, min_val, max_val)

    try:
        value = int(value, 8)
    except ValueError:
        raise validate.VdtTypeError(value)
    return validate.is_integer(value, min_val, max_val)

def is_logging_level(value):
    """
    Coerces a string to an integer logging level which
    maps to a standard python logging level
    """
    try:
        level = format_loglevel(value)
    except:
        raise validate.VdtTypeError(value)

    return level

def is_cmdline(value):
    """
    Parse command line input
    """
    try:
        return shlex.split(value)
    except:
        raise validate.VdtTypeError(value)

VALIDATOR = Validator({
    'octal' : is_octal,
    'logging_level' : is_logging_level,
    'coerced_list' : is_coerced_list,
    'cmd_args' : is_cmdline
})
