from configobj import ConfigObj, Section
from validate import Validator

class BaseConfig(ConfigObj):
    """Config class"""
    def __init__(self, *args, **kwargs):
        ConfigObj.__init__(self,
                           interpolation=False,
                           write_empty_values=True,
                           encoding='utf8',
                           *args, **kwargs)

    def validate_config(self, configspec, validation_functions=None):
        self._handle_configspec(configspec)
        self.validate(Validator(validation_functions), copy=True)

class Configspec(ConfigObj):
    """Specification for a configuration

    This should follow the standard format of an ini
    file but the values are spec definitions that define
    what valid values are for the associated keys.

    Example:
    [myconfig]
    foo = integer(min=2,max=42, default=3)
    """
    def __init__(self, value=None):
        ConfigObj.__init__(self,
                           value,
                           list_values=False,
                           interpolation=False)

#: configspec that every backupset should implement
std_backup_spec = Configspec("""
[holland:backup]
plugin                  = string
auto-purge-failures     = boolean(default=yes)
purge-policy            = option(manual,before-backup,after-backup,default=after-backup)
backups-to-keep         = integer(default=1)
estimated-size-factor   = float(default=1.0)
fail-backup             = force_list(default=list())
pre-backup              = force_list(default=list())
post-backup             = force_list(default=list())
""".strip().splitlines())

def load_config(path):
    """Load the configuration from the file path"""
    cfg = BaseConfig(path, file_error=True)
    # normalize _ => - in keys; foo-bar = foo_bar

    def normalize(section, key):
        """Normalize a key in a configuration file

        This presently treats _ as equivalent to - by always
        configured '_' to '-'.

        Normalizations also always makes keys non-unicode strings
        to be compatible with older versions of python that don't
        accept unicode keys in **kwargs (<=cpython2.5)
        """
        section.rename(key, str(key.replace('_', '-')))

    cfg.walk(normalize, call_on_sections=True)
    return cfg
