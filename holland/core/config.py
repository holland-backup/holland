from configobj import ConfigObj
from validate import Validator

class HollandConfig(ConfigObj):
    def validate_config(self, configspec, validation_functions=None):
        self._handle_configspec(configspec)
        self.validate(Validator(validation_functions), copy=True)

def load_config(path):
    return HollandConfig(path, file_error=True)
