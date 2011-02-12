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

class BaseValidator(object):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

    def normalize(self, value):
        "Normalize a string value"
        if isinstance(value, basestring):
            return unquote(value)
        else:
            return value

    def convert(self, value):
        """Convert a value from its string representation to a python
        object.

        """
        return value

    def validate(self, value):
        """Validate a value and return its conversion

        :raises: ValidatorError on failure
        """
        value = self.normalize(value)
        value = self.convert(value)
        return value

    def format(self, value):
        """Format a value as it should be written in a config file"""
        return str(value)

class ValidationError(ValueError):
    """Raised when validation fails"""
    def __init__(self, message, value):
        ValueError.__init__(self, message)
        self.value = value

    def __str__(self):
        return self.message

class BoolValidator(BaseValidator):
    def convert(self, value):
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

class FloatValidator(BaseValidator):
    def convert(self, value):
        try:
            return float(value)
        except ValueError, exc:
            raise ValidatorError(str(exc), value)

    def format(self, value):
        return "%.2f" % value

class IntValidator(BaseValidator):
    # XXX: support min,max
    def convert(self, value):
        if isinstance(value, int):
            return value
        if value is None:
            return value
        try:
            return int(value, self.kwargs.get('base', 10))
        except ValueError, exc:
            raise ValidatorError("Invalid format for integer %s" % value, value)

    def format(self, value):
        if value is None:
            return value
        return str(value)

class StringValidator(BaseValidator):
    def convert(self, value):
        return value

    def format(self, value):
        return value

class OptionValidator(BaseValidator):
    def convert(self, value):
        if value in self.args:
            return value
        raise ValidatorError("invalid option %r" % value, value)

    def format(self, value):
        return str(value)


class ListValidator(BaseValidator):

    #@staticmethod
    def _utf8_encode(unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')
    _utf8_encode = staticmethod(_utf8_encode)

    def normalize(self, value):
        "Normalize a value"
        # skip BaseValidator's unquoting behavior
        return value

    def convert(self, value):
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

class TupleValidator(ListValidator):
    def convert(self, value):
        value = super(TupleValidator, self).convert(value)
        return tuple(value)


class CmdlineValidator(BaseValidator):
    def convert(self, value):
        return [arg.decode('utf8') for arg in shlex.split(value.encode('utf8'))]

    def format(self, value):
        return subprocess.list2cmdline(value)


class LogLevelValidator(BaseValidator):
    def convert(self, value):
        if isinstance(value, int):
            return value
        try:
            return logging._levelNames[value.upper()]
        except KeyError:
            raise ValidatorError("Invalid log level '%s'" % value, value)

    def format(self, value):
        try:
            return logging._levelNames[value].lower()
        except KeyError:
            raise ValidatorError("Unknown logging level '%s'" % value, value)

default_validators = (
    ('boolean', BoolValidator),
    ('integer', IntValidator),
    ('float', FloatValidator),
    ('string', StringValidator),
    ('option', OptionValidator),
    ('list', ListValidator),
    ('force_list', ListValidator),
    ('tuple', TupleValidator),
    ('cmdline', CmdlineValidator),
    ('log_level', LogLevelValidator),
)
