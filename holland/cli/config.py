import logging
from holland.core import Config, Configspec
from holland.core import load_plugin

LOG = logging.getLogger(__name__)

cli_configspec = Configspec.parse("""
[holland]
backup-directory = string(default='.')
backupsets       = force_list(default=list())
umask            = integer(default='0007', base=8)
path             = string(default=None)
tmpdir           = string(default=None)

[logging]
file             = string(default='/var/log/holland/holland.log')
format           = string(default='[%(levelname)s] %(message)s')
level            = log_level(default="info")
""".splitlines())

def load_global_config(path):
    if path:
        cfg = Config.read([path])
    else:
        cfg = Config()

    cli_configspec.validate(cfg)
    return cfg
