"""This module contains standard checks for Configspec values"""

import csv
import logging
try:
    from io import StringIO, BytesIO
except ImportError: #pragma: no cover
    from StringIO import StringIO
    BytesIO = StringIO
import shlex
import subprocess
from holland.core.config.util import unquote

class BaseCheck(object):
    def normalize(self, value):
        "Normalize a string value"
        if isinstance(value, basestring):
            return unquote(value)
        else:
            return value

    def check(self, value):
        """Check a value and return its conversion

        :raises: CheckError on failure
        """
        return value

    def format(self, value):
        """Format a value as it should be written in a config file"""
        return str(value)

class CheckError(ValueError):
    "Raised when a check fails"
    def __init__(self, message, value):
        ValueError.__init__(self, message)
        self.value = value

    def __str__(self):
        return self.message

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
        if isinstance(value, bool):
            return value
        return valid_bools[value.lower()]

    def format(self, value):
        return value and 'yes' or 'no'

class FloatCheck(BaseCheck):
    def check(self, value):
        try:
            return float(value)
        except ValueError, exc:
            raise CheckError(str(exc), value)

    def format(self, value):
        return "%.2f" % value

class IntCheck(BaseCheck):
    def __init__(self, min=None, max=None, base=10):
        self.min = min
        self.max = max
        self.base = base

    def check(self, value):
        if isinstance(value, int):
            return value
        if value is None:
            return value
        try:
            return int(value, self.base)
        except ValueError, exc:
            raise CheckError("Invalid format for integer %s" % value, value)

    def format(self, value):
        if value is None:
            return value
        return str(value)

class StringCheck(BaseCheck):
    def check(self, value):
        return value

    def format(self, value):
        return value

class OptionCheck(BaseCheck):
    def __init__(self, *args, **kwargs):
        self.options = args

    def check(self, value):
        if value in self.options:
            return value
        raise CheckError("invalid option %r" % value, value)

    def format(self, value):
        return str(value)


class ListCheck(BaseCheck):

    #@staticmethod
    def _utf8_encode(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')
    _utf8_encode = staticmethod(_utf8_encode)

    def normalize(self, value):
        "Normalize a value"
        # skip BaseCheck's unquoting behavior
        return value

    def check(self, value):
        if isinstance(value, list):
            return value
        data = self._utf8_encode(StringIO(value))
        reader = csv.reader(data, dialect='excel', delimiter=',',
                skipinitialspace=True)
        return [unquote(cell.decode('utf8')) for row in reader for cell in row
                 if unquote(cell.decode('utf8'))]

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
        return [arg.decode('utf8') for arg in shlex.split(value.encode('utf8'))]

    def format(self, value):
        return subprocess.list2cmdline(value)


class LogLevelCheck(BaseCheck):
    def check(self, value):
        if isinstance(value, int):
            return value
        try:
            return logging._levelNames[value.upper()]
        except KeyError:
            raise CheckError("Invalid log level '%s'" % value, value)

    def format(self, value):
        try:
            return logging._levelNames[value].lower()
        except KeyError:
            raise CheckError("Unknown logging level '%s'" % value, value)

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
    ('log_level', LogLevelCheck),
)
