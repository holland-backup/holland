"""Load a holland.conf config file"""
import os
import logging
from holland.core import Config, Configspec, ConfigError, BackupPlugin

LOG = logging.getLogger(__name__)

cli_configspec = Configspec.parse("""
[holland]
backup-directory = string(default=None)
backupsets       = force_list(default=list())
umask            = integer(default='0007', base=8)
path             = string(default=None)
tmpdir           = string(default=None)

[logging]
file             = string(default='/var/log/holland/holland.log')
format           = string(default='[%(levelname)s] %(message)s')
level            = log_level(default="info")
""".splitlines())

class GlobalHollandConfig(Config):
    name = None

    def basedir(self):
        return os.path.abspath(os.path.dirname(self.name or '.'))

    def load_backupset(self, name):
        if not os.path.isabs(name):
            name = os.path.join(self.basedir(), 'backupsets', name)

        if not os.path.isdir(name) and not name.endswith('.conf'):
            name += '.conf'

        cfg = Config.read([name])

        # load providers/$plugin.conf if available
        plugin = cfg.get('holland:backup', {}).get('plugin')
        if plugin:
            provider_path = os.path.join(self.basedir(),
                                         'providers',
                                         plugin + '.conf')
            try:
                cfg.meld(Config.read([provider_path]))
            except ConfigError:
                LOG.debug("No global provider found.  Skipping.")
        cfg.name = os.path.splitext(os.path.basename(name))[0]
        # validate the holland:backup section
        BackupPlugin.configspec().validate(cfg, ignore_unknown_sections=True)
        return cfg

    #@classmethod
    def configspec(self):
        return cli_configspec
    configspec = classmethod(configspec)

def load_global_config(path):
    if path:
        try:
            cfg = GlobalHollandConfig.read([path])
            cfg.name = path
        except ConfigError, exc:
            LOG.error("Failed to read %s: %s", path, exc)
            cfg = GlobalHollandConfig()
    else:
        cfg = GlobalHollandConfig()

    cfg.configspec().validate(cfg)
    return cfg
