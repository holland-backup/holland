"""This module provides support for configs that validate other configs"""
from config import Config, ConfigError, BaseFormatter
from parsing import CheckParser
from checks import builtin_checks

class CheckFormatter(BaseFormatter):
    def __init__(self, configspec):
        self.configspec = configspec

    def format(self, key, value):
        try:
            name, args, kwargs = CheckParser.parse(self.configspec[key])
            check = self.configspec.registry[name](*args, **kwargs)
            return check.format(value)
        except KeyError:
            return value

class ValidationError(ConfigError):
    """Raise when a check fails to validate properly"""

class Configspec(Config):
    """A configuration that can validate other configurations
    """
    #: registry dictionary for resolving checks
    registry = ()

    def __init__(self, *args, **kwargs):
        super(Configspec, self).__init__(*args, **kwargs)
        self.registry = dict(builtin_checks)

    #XXX: improve docstring
    def validate(self, config):
        """Validate a config against this configspec.

        This method modifies ``config`` replacing option values with the
        conversion provided by the associated check.

        :param config: config instance to validate
        :returns: validated config
        """
        for key, value in self.iteritems():
            #XXX: value must be a Configspec if we want
            #     to recurse to more than 1 level
            if isinstance(value, dict):
                # recurse to section
                try:
                    cfgsect = config[key]
                except KeyError:
                    cfgsect = config.setdefault(key, config.__class__())
                if not isinstance(value, Configspec):
                    value = Configspec(value)
                value.validate(cfgsect)
                if isinstance(config, Config):
                    cfgsect.formatter = CheckFormatter(value)
            else:
                name, args, kwargs = CheckParser.parse(value)
                check = self.registry[name](*args, **kwargs)
                value = check.normalize(value)
                try:
                    value = config[key]
                except KeyError:
                    value = kwargs.get('default')
                config[key] = check.check(value)
        if isinstance(config, Config):
            config.formatter = CheckFormatter(self)
        return config
