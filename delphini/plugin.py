"""MySQL Cluster backups"""

import os
import logging
from holland.core.exceptions import BackupError
from delphini.spec import CONFIGSPEC
from delphini.util import backup, ClusterError

LOG = logging.getLogger(__name__)

def stream_factory(base_path, method, level):
    from holland.lib.compression import open_stream

    def stream_open(path, mode):
        real_path = os.path.join(base_path, path)
        return open_stream(real_path, mode, method, level)
    return stream_open

class DelphiniPlugin(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        config.validate_config(self.configspec())
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        # XXX: implement I_S querying or ssh du -sh perhaps
        return 0

    def backup(self):
        config = self.config['mysql-cluster']
        dsn = config['connect-string']
        ssh_user = config['default-ssh-user']
        ssh_keyfile = config['default-ssh-keyfile']
        stream_open = stream_factory(self.target_directory,
                                     self.config['compression']['method'],
                                     self.config['compression']['level'])
        try:
            backup(dsn, ssh_user, ssh_keyfile, stream_open)
        except ClusterError, exc:
            raise BackupError(exc)

    def configspec(self):
        return CONFIGSPEC

    def info(self):
        return ""
