"""
Extra check methods to work with
a validate.py Validator instance
"""

import logging
import shlex
from builtins import str
from io import StringIO
from . import validate as validate
from .validate import Validator

def is_coerced_list(value, min_val=None, max_val=None):
    """
    Checks if a value is a list, if not coerces
    it to a list
    """
    if isinstance(value, str):
        value = [value]
    return validate.is_list(value, min_val, max_val)

def is_octal(value, min_val=None, max_val=None):
    """
    Coerces a value to octal
    """
    if not isinstance(value, str):
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
    std_levels = {
        'debug'     : logging.DEBUG,
        'info'      : logging.INFO,
        'warning'   : logging.WARNING,
        'error'     : logging.ERROR,
        'critical'  : logging.CRITICAL
    }
    
    try:
        level = value.lower().strip()
    except:
        raise validate.VdtTypeError(value)
    
    if not std_levels.get(level):
        raise validate.ValidateError(value)
    
    return std_levels.get(level)

def is_cmdline(value):
    try:
        return shlex.split(value)
    except:
        raise validate.VdtTypeError(value)

validator = Validator({
    'octal' : is_octal,
    'logging_level' : is_logging_level,
    'coerced_list' : is_coerced_list,
    'cmd_args' : is_cmdline
})
