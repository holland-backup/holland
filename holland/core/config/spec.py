"""
    holland.core.config.spec
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Support for defining valid config parameters and values and validating
    candidate configs

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import logging
from holland.core.config.config import Config, BaseFormatter
from holland.core.config.check import Check, CheckError
from holland.core.config.validation import default_validators, ValidationError
from holland.core.config.util import missing

LOG = logging.getLogger(__name__)

class ValidateError(ValueError):
    """Raised when one or more errors are encountered during
    Configspec.validate()

    """
    def __init__(self, errors):
        ValueError.__init__(self)
        self.errors = errors

    def __repr__(self):
        result = [
            "%d validation errors encountered" % len(self.errors)
        ]
        for error, source in self.errors:
            if source:
                lines = source[1:]
                if lines[0] != lines[-1]:
                    lines = "-".join([str(x) for x in lines])
                else:
                    lines = str(lines[-1])
                result.append("%s line %s: %s" % (source[0], lines, error))
            else:
                result.append("%s" % error)
        return "\n".join(result)

    __str__ = __repr__

class CheckFormatter(BaseFormatter):
    """Format a ``Config`` instance based on
    the validators associated with a Configspec
    """

    def __init__(self, configspec):
        BaseFormatter.__init__(self)
        self.configspec = configspec

    def format(self, key, value):
        """Format an option/value pair based on the
        associated Validator's format method

        :returns: formatted value string
        """
        try:
            check = Check.parse(self.configspec.get(key, ''))
        except CheckError:
            return value

        try:
            validator = self.configspec.registry[check.name]
            validator = validator(check.args, check.kwargs)
            return validator.format(value)
        except KeyError:
            return value

class Configspec(Config):
    """A configuration that can validate other configurations
    """
    #: registry dictionary for resolving checks
    registry = ()

    def __init__(self, *args, **kwargs):
        super(Configspec, self).__init__(*args, **kwargs)
        self.registry = dict(default_validators)

    def validate(self, config, ignore_unknown_sections=False):
        """Validate a config against this configspec.

        This method modifies ``config`` replacing option values with the
        conversion provided by the associated check.

        :param config: config instance to validate
        :returns: validated config
        """
        errors = []
        if not isinstance(config, Config):
            config = Config(config)

        for key, value in self.iteritems():
            if isinstance(value, dict):
                try:
                    self._validate_section(key, config)
                except ValidateError, exc:
                    errors.extend(exc.errors)
            else:
                try:
                    self._validate_option(key, value, config)
                except ValidationError, exc:
                    errors.append((exc, config.source.get(key, None)))

        self.check_missing(config, ignore_unknown_sections)
        config.formatter = CheckFormatter(self)
        if errors:
            raise ValidateError(errors)
        return config

    def _validate_section(self, key, config):
        """Validate a subsection """
        try:
            cfgsect = config[key]
        except KeyError:
            # missing section in config that we are validating
            cfgsect = config.setdefault(key, config.__class__())
            cfgsect.name = key

        # ensure we are always validating a Config instance
        if not isinstance(cfgsect, Config):
            cfgsect = config.__class__(cfgsect)
            config[key] = cfgsect

        check = self[key]
        # handle raw dict objects as configspec input
        if not isinstance(check, Configspec):
            check = self.__class__(check)

        # recurse to the Configspec subsection
        check.validate(cfgsect)

    def _resolve_value(self, key, check, config):
        """Resolve a value for a given key

        This will find where a value is defined or raise an error if no such
        key exists.  This looks for the value in the following places:

        * Use the original config's value if one was specified
        * if the config did not have a value, attempt to use the aliasof value
        * if the key is not aliased then use the default value provided by the
          check
        * if no value at all is specified and there is no default for the check
          raise a ValidationError
        """
        value = config.get(key, missing)
        # if no value for the key was provided in the config try its
        # alias, if one exists
        if value is missing and check.aliasof is not missing:
            value = config.get(check.aliasof, missing)
        # if no alias was found, try the default
        if value is missing:
            value = check.default
        # if not even a default value, raise an error noting this option is
        # required
        if value is missing:
            raise ValidationError("Option '%s' requires a specified value" %
                                  key, None)
        return value

    def _validate_option(self, key, checkstr, config):
        """Validate a single option for this configspec"""
        try:
            check = Check.parse(checkstr)
        except CheckError:
            raise ValidationError("Internal Error.  Failed to parse a "
                                  "validation check '%s'" % checkstr, checkstr)

        validator = self.registry[check.name](check.args, check.kwargs)
        value = self._resolve_value(key, check, config)
        try:
            value = validator.validate(value)
        except ValidationError, exc:
            raise ValidationError("%s.%s : %s" % (config.name, key, exc), exc.value)
            
        config[key] = value
        if check.aliasof is not missing:
            config.rename(key, check.aliasof)


    def check_missing(self, config, ignore_unknown_sections):
        """Check for values in config with no corresponding configspec entry

        These are either bugs in the configspec or simply typos or invalid
        options.
        """
        for key in config:
            if key not in self:
                if isinstance(config[key], dict):
                    if ignore_unknown_sections:
                        continue
                    source, lineno = config.source[key]
                    LOG.warn("Unknown section [%s]: %s line %d", key, source,
                            lineno)
                else:
                    source, start, end = config.source[key]
                    if start == end:
                        line_range = "line %d" % start
                    else:
                        line_range = "lines %d-%d" % (start, end)
                    LOG.warn("Unknown option %s in [%s] %s %s", key,
                            config.name, source, line_range)
