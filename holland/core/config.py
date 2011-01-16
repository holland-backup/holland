from configobj import ConfigObj, Section
from validate import Validator

class BaseConfig(ConfigObj):
    def __init__(self, *args, **kwargs):
        ConfigObj.__init__(self,
                           list_values=False,
                           interpolation=False,
                           write_empty_values=True,
                           encoding='utf8',
                           *args, **kwargs)

    def validate_config(self, configspec, validation_functions=None):
        self._handle_configspec(configspec)
        self.validate(Validator(validation_functions), copy=True)

class Configspec(ConfigObj):
    def __init__(self, value):
        ConfigObj.__init__(self,
                           value,
                           list_values=False,
                           interpolation=False)

def load_config(path):
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
