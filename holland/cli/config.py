import logging
from configobj import ConfigObj, get_extra_values
from validate import Validator, ValidateError, VdtTypeError
from holland.core import load_plugin

LOG = logging.getLogger(__name__)

cli_configspec = """
[holland]
backup-directory = string(default='.')
backupsets       = force_list(default=())
umask            = octal(default=None)
path             = string(default=None)
tmpdir           = string(default=None)

[logging]
file             = string(default='/var/log/holland/holland.log')
format           = string(default='[%(levelname)s] %(message)s')
level            = log_level(default=info)
""".strip().splitlines()

def is_octal(value):
    try:
        return int(value, 8)
    except ValueError:
        raise VdtTypeError(value)

def is_log_level(value):
    if not isinstance(value, basestring):
        raise VdtTypeError(value)
    try:
        return logging._levelNames[value.upper()]
    except KeyError:
        raise VdtTypeError(value)

def load_config(path, configspec=None, validator=Validator()):
    config = ConfigObj(path,
                       configspec=ConfigObj(configspec,
                                            list_values=False,
                                            interpolation=False),
                       file_error=True,
                       encoding='utf8',
                       interpolation=False)

    if configspec:
        config.validate(validator, copy=True)

    return config

def load_global_config(path):
    holland_validator = Validator({
        'octal' : is_octal,
        'log_level' : is_log_level,
    })
    return load_config(path,
                       configspec=cli_configspec,
                       validator=holland_validator)

def load_backup_config(path, provider=None):
    """Load a backup configuration

    If ``provider`` is specified, the backup config is
    merged with the provider

    If the plugin specified in the backup config has
    a configspec, the config will be validated against that
    """
    backup_cfg = load_config(path)
    if provider:
        provider_cfg = load_config(provider)
        provider_cfg.merge(backup_cfg)
        backup_cfg = provider_cfg

    plugincls = load_plugin('holland.backup',
                            backup_cfg['holland:backup']['plugin'])
    configspec = plugincls.configspec()
    return load_config(backup_cfg, configspec)
