"""This module provides support for configs that validate other configs"""

import logging
import warnings
from holland.core.config.config import Config, ConfigError, BaseFormatter
from holland.core.config.check import Check, CheckError
from holland.core.config.validation import default_validators, ValidationError
from holland.core.config.util import missing

LOG = logging.getLogger(__name__)

class ValidateError(ValueError):
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
    def __init__(self, configspec):
        self.configspec = configspec

    def format(self, key, value):
        try:
            check = Check.parse(self.configspec[key])
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
                    self.validate_section(key, config)
                except ValidateError, exc:
                    errors.extend(exc.errors)
            else:
                try:
                    self.validate_option(key, value, config)
                except ValidationError, exc:
                    errors.append((exc, config.source.get(key, None)))

        for key in config:
            if key not in self:
                if isinstance(config[key], dict) and ignore_unknown_sections:
                    continue
                warnings.warn("Unknown option %s in [%s]" %
                              (key, config.name))
        config.formatter = CheckFormatter(self)
        if errors:
            raise ValidateError(errors)
        return config

    def validate_section(self, key, config):
        """Validate a subsection """
        try:
            cfgsect = config[key]
        except KeyError:
            # missing section in config that we are validating
            cfgsect = config.setdefault(key, config.__class__())

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

    def validate_option(self, key, checkstr, config):
        """Validate a single option for this configspec"""
        check = Check.parse(checkstr)
        validator = self.registry[check.name](check.args, check.kwargs)
        value = self._resolve_value(key, check, config)
        value = validator.validate(value)
        config[key] = value
        if check.aliasof is not missing:
            config.rename(key, check.aliasof)


