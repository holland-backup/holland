"""This module provides support for configs that validate other configs"""

import logging
from config import Config, ConfigError, BaseFormatter
from parsing import CheckParser
from checks import builtin_checks, CheckError

LOG = logging.getLogger(__name__)

class Missing(object):
    def __str__(self):
        return '<missing value>'
    __repr__ = __str__

missing = Missing()
del Missing

class CheckFormatter(BaseFormatter):
    def __init__(self, configspec):
        self.configspec = configspec

    def format(self, key, value):
        try:
            name, args, kwargs = CheckParser.parse(self.configspec[key])
            default = kwargs.pop('default', None)
            aliasof = kwargs.pop('aliasof', None)
            check = self.configspec.registry[name](*args, **kwargs)
            return check.format(value)
        except KeyError:
            return value

class ValidationError(ConfigError):
    """Raise when a check fails to validate properly"""
    def __init__(self, errors):
        self.errors = errors

class Configspec(Config):
    """A configuration that can validate other configurations
    """
    #: registry dictionary for resolving checks
    registry = ()

    def __init__(self, *args, **kwargs):
        super(Configspec, self).__init__(*args, **kwargs)
        self.registry = dict(builtin_checks)

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
                    errors.append(exc.errors)
                cfgsect.formatter = CheckFormatter(check)
            else:
                # parse the check
                name, args, kwargs = CheckParser.parse(check)
                default = kwargs.pop('default', missing)
                alias = kwargs.pop('aliasof', None)
                check = self.registry[name](*args, **kwargs)

                # get the value if the config if it exists
                try:
                    value = config[key]
                except KeyError:
                    # use check's default value otherwise
                    value = default
                # if no default and no value specified it will be a missing
                # required value
                if value is missing:
                    errors.append(CheckError("Required value for %r", key))
                    continue

                value = check.normalize(value)
                # perform check
                try:
                    result = check.check(value)
                except CheckError, exc:
                    errors.append(exc)
                    continue
                # update config with result of check (unserialized value)
                config[key] = result
                # handle aliasing of keys to other keys
                if alias:
                    config.rename(key, alias)
        config.formatter = CheckFormatter(self)
        if errors:
            raise ValidationError(errors)
        return config
