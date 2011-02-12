"""This module provides support for configs that validate other configs"""

import logging
from config import Config, ConfigError, BaseFormatter
from holland.core.config.check import Check, CheckError
from holland.core.config.validation import default_validators, ValidationError
from holland.core.config.util import missing

LOG = logging.getLogger(__name__)

class ValidateError(ValueError):
    def __init__(self, errors):
        ValueError.__init__(self)
        self.errors = errors

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

    def validate(self, config):
        """Validate a config against this configspec.

        This method modifies ``config`` replacing option values with the
        conversion provided by the associated check.

        :param config: config instance to validate
        :returns: validated config
        """
        errors = []
        if not isinstance(config, Config):
            config = Config(config)

        for key, check in self.iteritems():
            if isinstance(check, dict):
                # recurse to section
                try:
                    cfgsect = config[key]
                except KeyError:
                    # missing section in config that we are validating
                    cfgsect = config.setdefault(key, config.__class__())

                # ensure we are always validating a Config instance
                if not isinstance(cfgsect, Config):
                    cfgsect = config.__class__(cfgsect)
                    config[key] = cfgsect

                # handle raw dict objects as configspec input
                if not isinstance(check, Configspec):
                    check = self.__class__(check)

                try:
                    check.validate(cfgsect)
                except ValidationError, exc:
                    errors.extend(exc.errors)
                cfgsect.formatter = CheckFormatter(check)
            else:
                # parse the check
                check = Check.parse(check)
                validator = self.registry[check.name](check.args, check.kwargs)

                # get the value if the config if it exists
                try:
                    value = config[key]
                except KeyError:
                    # use check's default value otherwise
                    try:
                        value = config[check.aliasof]
                    except KeyError:
                        value = check.default
                # if no default and no value specified it will be a missing
                # required value
                if value is missing:
                    errors.append(CheckError("Required value for %r" % key))
                    continue

                # perform check
                try:
                    result = validator.validate(value)
                except ValidationError, exc:
                    errors.append(exc)
                    continue
                # update config with result of check (unserialized value)
                config[key] = result
                # handle aliasing of keys to other keys
                if check.aliasof is not missing:
                    config.rename(key, check.aliasof)
        config.formatter = CheckFormatter(self)
        if errors:
            raise ValidationError(errors)
        return config
