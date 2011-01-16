"Formatting utility functions"

from math import floor, log
from time import strftime, localtime

def format_interval(seconds):
    "Format an integer number of seconds to a human readable string."
    units = [
        (('week', 'weeks'), 604800),
        (('day', 'days'), 86400),
        (('hour', 'hours'), 3600),
        (('minute', 'minutes'), 60),
        #(('second', 'seconds'), 1)
    ]
    result = []
    for names, value in units:
        quotient, seconds = divmod(seconds, value)
        if quotient > 0:
            plural = bool(quotient > 1)
            result.append('%d %s' % (quotient, names[plural]))
    if seconds:
        result.append("%.2f %s" %
                      (seconds, ['second', 'seconds'][seconds != 1.0]))
    return ', '.join(result)

def format_datetime(epoch, format="%a %b %d %Y %I:%M:%S%p"):
    "Format a datetime from an integer epoch"
    return strftime(format, localtime(epoch))

def format_bytes(nbytes, precision=2):
    "Format an integer number of bytes to a human readable string."

    if nbytes != 0:
        exponent = floor(log(abs(nbytes), 1024))
    else:
        exponent = 0

    return "%.*f%s" % (
        precision,
        nbytes / (1024 ** exponent),
        ['B','KB','MB','GB','TB','PB','EB','ZB','YB'][int(exponent)]
    )

def format_loglevel(str_level):
    """
    Coerces a string to an integer logging level which
    maps to a standard python logging level
    """
    import logging
    std_levels = {
        'debug'     : logging.DEBUG,
        'info'      : logging.INFO,
        'warning'   : logging.WARNING,
        'error'     : logging.ERROR,
        'critical'  : logging.CRITICAL
    }

    level = str_level.lower().strip()

    return std_levels.get(level)
