"""
Format day, byt, number, and log objects
"""

import logging
import math
from time import localtime, strftime


def format_interval(seconds):
    """
    Format an integer number of seconds to a human readable string.
    """
    units = [
        (("week", "weeks"), 604800),
        (("day", "days"), 86400),
        (("hour", "hours"), 3600),
        (("minute", "minutes"), 60),
        # (('second', 'seconds'), 1)
    ]
    result = []
    for names, value in units:
        num, seconds = divmod(seconds, value)
        if num > 0:
            result.append(f"{num} {names[num > 1]}")
    if seconds:
        ret = ["second", "seconds"][seconds != 1.0]
        result.append(f"{seconds:.2f} {ret}")
    return ", ".join(result)


def format_datetime(epoch):
    """
    Define standard datetime string
    """
    return strftime("%a %b %d %Y %I:%M:%S%p", localtime(epoch))


def format_bytes(input_bytes):
    """
    Format an integer number of input_bytes to a human readable string.
    """
    if input_bytes < 0:
        raise ArithmeticError("Only Positive Integers Allowed")

    if input_bytes != 0:
        exponent = float(math.floor(math.log(input_bytes, 1024)))
    else:
        exponent = float(0)

    ret = input_bytes / (1024 ** exponent)
    postfix = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][int(exponent)]
    return f"{ret:.2f}{postfix}"


def format_loglevel(str_level):
    """
    Coerces a string to an integer logging level which
    maps to a standard python logging level
    """
    std_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    level = str_level.lower().strip()

    return std_levels.get(level)
