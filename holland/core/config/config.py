"""
Configuration API support
"""

import logging
import os

from .checks import VALIDATOR

# get_extra_values was added in configobj 4.7. EL6 ships with 4.6
# Try to import this and remove get_extra_values if it doesn't work
try:
    from configobj import ConfigObj, Section, flatten_errors, get_extra_values
except ImportError:
    from configobj import ConfigObj, Section, flatten_errors


LOG = logging.getLogger(__name__)

CONFIG_SUFFIX = ".conf"

# Main Holland configspec
CONFIGSPEC = """
[holland]
tmpdir              = string(default=None)
plugin-dirs         = coerced_list(default=list('/usr/share/holland/plugins'))
backup-directory    = string(default=/var/spool/holland)
backupsets          = coerced_list(default=list())
umask               = octal(default='007')
path                = string(default=None)

[logging]
level               = logging_level(default='info')
filename            = string(default=None)
format              = string(default=None)
""".splitlines()


class ConfigError(Exception):
    """
    Define  exceptoin for configuration errors
    """


class BaseConfig(ConfigObj):
    """
    Provides basic configuration support.  This
    is a subclass of ConfigObj but adds a few
    extra convenient method.
    """

    def __init__(self, path, configspec=None, file_error=True):
        ConfigObj.__init__(
            self,
            path,
            file_error=file_error,
            interpolation=False,
            write_empty_values=True,
            encoding="utf8",
            default_encoding="utf8",
            configspec=configspec,
        )

    @staticmethod
    def _canonicalize(section, key):
        """Rewrite all keys so that underscores are normalized to dashes"""
        section.rename(key, str(key.replace("_", "-")))

    def reload(self):
        """Reloads ConfigObj from filesystem, then recursively walks each
        section.
        """
        ConfigObj.reload(self)
        self.walk(self._canonicalize, call_on_sections=True)

    def validate_config(self, configspec, suppress_warnings=False):
        """
        Validate this config with the given configspec
        """
        self._handle_configspec(configspec)
        errors = self.validate(VALIDATOR, preserve_errors=True)
        for entry in flatten_errors(self, errors):
            section_list, key, error = entry
            if not error:
                LOG.error("Missing parameter %s", ".".join(section_list + [key]))
            else:
                LOG.error("Configuration error %s: %s", ".".join(section_list + [key]), error)

        # warn about any unknown parameters before we potentially abort on
        # validation errors
        # get_extra_values is not available in EL6 version of configobj
        if not suppress_warnings:
            try:
                for sections, name in get_extra_values(self):
                    LOG.warning("Unknown parameter '%s' in section '%s'", name, ".".join(sections))
            except NameError:
                pass

        if errors is not True:
            raise ConfigError(
                f"Configuration errors were encountered while validating {self.filename}"
            )
        return errors

    def lookup(self, key, safe=True):
        """
        Lookup a configuration item based on the
        dot-separated path.
        """
        parts = key.split(".")
        # lookup key as a . separated hierarchy path
        section = self
        result = None
        count = 0
        for count, name in enumerate(parts):
            if not isinstance(section, Section):
                result = None
                break
            result = section.get(name)
            section = result
        if not result and not safe:
            raise KeyError(f"{key} not found ({parts[count]})")
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result


class BackupConfig(BaseConfig):
    """
    Load config for a backupset and merge with
    its provider config
    """

    def __init__(self, path):
        BaseConfig.__init__(self, None)
        basecfg = BaseConfig(path)
        basecfg.walk(self._canonicalize, call_on_sections=True)
        provider = basecfg.lookup("holland:backup.plugin")
        if provider:
            try:
                configbase = os.path.dirname(os.path.dirname(path))
                providerpath = os.path.join(configbase, "providers", provider)
                providerpath += CONFIG_SUFFIX
                providercfg = BaseConfig(providerpath)
                providercfg.walk(self._canonicalize, call_on_sections=True)
                self.merge(providercfg)
            except IOError as ex:
                LOG.warning("Failed to load config for provider %r (%s)", provider, ex)
        self.merge(basecfg)
        self.filename = basecfg.filename


class GlobalConfig(BaseConfig):
    """
    Load Holland's global config.
    """

    def __init__(self, filename):
        if filename:
            self.filename = os.path.abspath(filename)
            self.configdir = os.path.dirname(self.filename)
        else:
            self.filename = None
            self.configdir = None
        BaseConfig.__init__(self, self.filename)

    def provider(self, name):
        """
        Load the provider config relative to this configs
        base directory
        """
        path = os.path.join(self.configdir, "providers", name) + CONFIG_SUFFIX
        return BaseConfig(path)

    def backupset(self, name):
        """
        Load the backupset config relative to this configs
        base directory
        """
        if not self.configdir:
            raise IOError("Config has not been initialized")
        path = os.path.join(self.configdir, "backupsets", name) + CONFIG_SUFFIX
        return BackupConfig(path)

    def hook_config(self, name):
        """
        This doesn't appear to be called anywhere and I'm not sure what it's for
        """
        for section_name in self:
            if not isinstance(self[section_name], Section):
                continue
            if section_name.startswith("hook:"):
                hook_name = section_name[len("hook:") :]
                if hook_name == name:
                    return BaseConfig(self[section_name])

        return None


HOLLANDCFG = GlobalConfig(None)


def load_backupset_config(name):
    """
    Pass name into class
    """
    return HOLLANDCFG.backupset(name)


def setup_config(config_file):
    """
    Configure the default HOLLANDCFG instance in this module
    """
    if not config_file:
        LOG.debug("load_config called with not configuration file")
        HOLLANDCFG.validate_config(CONFIGSPEC)
        LOG.debug(repr(HOLLANDCFG))
        return None

    config_file = os.path.abspath(config_file)
    LOG.debug("Loading %r", config_file)
    HOLLANDCFG.clear()
    HOLLANDCFG.filename = config_file
    HOLLANDCFG.reload()
    HOLLANDCFG.validate_config(CONFIGSPEC)
    HOLLANDCFG.configdir = os.path.dirname(config_file)

    return None
