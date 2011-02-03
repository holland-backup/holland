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

def format_datetime(epoch, fmt="%a %b %d %Y %I:%M:%S%p"):
    "Format a datetime from an integer epoch"
    return strftime(fmt, localtime(epoch))

def format_bytes(nbytes, precision=2):
    "Format an integer number of bytes to a human readable string."

    if nbytes != 0:
        exponent = floor(log(abs(nbytes), 1024))
    else:
        exponent = 0

    try:
        return "%.*f%s" % (
            precision,
            nbytes / (1024 ** exponent),
            ['B','KB','MB','GB','TB','PB','EB','ZB','YB'][int(exponent)]
        )
    except IndexError:
        raise ArithmeticError("format_bytes() cannot format values beyond "
                              "yottabytes. Got: %d" % nbytes)
