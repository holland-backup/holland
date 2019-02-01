"""
Format day, byt, number, and log objects
"""


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
            result.append("%d %s" % (num, names[num > 1]))
    if seconds:
        result.append("%.2f %s" % (seconds, ["second", "seconds"][seconds != 1.0]))
    return ", ".join(result)


def format_datetime(epoch):
    """
    Define standard datetime string
    """
    from time import strftime, localtime

    return strftime("%a %b %d %Y %I:%M:%S%p", localtime(epoch))


def format_bytes(input_bytes, precision=2):
    """
    Format an integer number of input_bytes to a human readable string.
    """
    import math

    if input_bytes < 0:
        raise ArithmeticError("Only Positive Integers Allowed")

    if input_bytes != 0:
        exponent = float(math.floor(math.log(input_bytes, 1024)))
    else:
        exponent = float(0)

    return "%.*f%s" % (
        precision,
        float(input_bytes) / (1024 ** exponent),
        ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][int(exponent)],
    )


def format_loglevel(str_level):
    """
    Coerces a string to an integer logging level which
    maps to a standard python logging level
    """
    import logging

    std_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    level = str_level.lower().strip()

    return std_levels.get(level)
