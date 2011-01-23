"""This module contains standard checks for Configspec values"""

import csv
try:
    from io import StringIO
except ImportError: #pragma: nocover
    from cStringIO import StringIO
from subprocess import list2cmdline
from shlex import split

class BaseCheck(object):
    def __init__(self, default=None):
        self.default = default

    def check(self, value):
        """Check a value and return its conversion

        :raises: CheckError on failure
        """
        return value

    def format(self, value):
        """Format a value as it should be written in a config file"""
        return str(value)

class BoolCheck(BaseCheck):
    def check(self, value):
        valid_bools = {
            'yes'  : True,
            'on'   : True,
            'true' : True,
            '1'    : True,
            'no'   : False,
            'off'  : False,
            'false': False,
            '0'    : False,
        }
        value = value or self.default
        return valid_bools[value.lower()]

    def format(self, value):
        return value and 'yes' or 'no'

class FloatCheck(BaseCheck):
    def check(self, value):
        return float(value)

    def format(self, value):
        return "%f" % value

class IntCheck(BaseCheck):
    def __init__(self, default=None, min=None, max=None, base=10):
        self.min = min
        self.max = max
        self.base = base
        self.default = default

    def check(self, value):
        value = value or self.default
        if isinstance(value, int):
            return value
        if value is None:
            return value
        return int(value, self.base)

    def format(self, value):
        return str(value)

class StringCheck(BaseCheck):
    def check(self, value, default=None):
        return value

    def format(self, value):
        return value

class OptionCheck(BaseCheck):
    def __init__(self, *args, **kwargs):
        self.options = args
        self.default = kwargs.get('default')

    def check(self, value):
        if value in self.options:
            return value
        raise ValueError("invalid option %r" % value)

    def format(self, value):
        return str(value)


class ListCheck(BaseCheck):

    #@staticmethod
    def _utf8_encode(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')
    _utf8_encode = staticmethod(_utf8_encode)

    def check(self, value):
        if isinstance(value, list):
            return value
        data = self._utf8_encode(StringIO(value))
        reader = csv.reader(data, dialect='excel', delimiter=',',
                skipinitialspace=True)
        return [cell.decode('utf8') for row in reader for cell in row ]

    def format(self, value):
        result = BytesIO()
        writer = csv.writer(result, dialect='excel')
        writer.writerow([cell.encode('utf8') for cell in value])
        return result.getvalue().decode('utf8').strip()

class TupleCheck(ListCheck):
    def check(self, value):
        value = super(TupleCheck, self).check(value)
        return tuple(value)


class CmdlineCheck(BaseCheck):
    def check(self, value):
        return [arg.decode('utf8') for arg in split(value.encode('utf8'))]

    def format(self, value):
        return list2cmdline(value)

builtin_checks = (
    ('boolean', BoolCheck),
    ('integer', IntCheck),
    ('float', FloatCheck),
    ('string', StringCheck),
    ('option', OptionCheck),
    ('list', ListCheck),
    ('force_list', ListCheck),
    ('tuple', TupleCheck),
    ('cmdline', CmdlineCheck),
)
