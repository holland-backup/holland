"""SQLite backup plugin for Holland."""

import os
import logging
from subprocess import Popen, PIPE

from holland.lib.compression import open_stream
from holland.core.exceptions import BackupError

LOG = logging.getLogger(__name__)

CONFIGSPEC="""
[sqlite]
databases = force_list(default=list())
binary = string(default=/usr/bin/sqlite3)

[compression]
method = option('none', 'gzip', 'pigz', 'bzip2', 'lzop', default='gzip')
level = integer(min=0, max=9, default=1)
""".splitlines()

class SQLitePlugin(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        LOG.info("Validating config: %s", self.name)
        LOG.debug("Validated config: %r", self.config)
        self.config.validate_config(CONFIGSPEC)

    def estimate_backup_size(self):
        """
        Return total estimated size of all databases we are backing up (does 
        not account for post-compression).
        """
        total_size = 0
        for db in self.config['sqlite']['databases']:
            path = os.path.abspath(os.path.expanduser(db))
            if not os.path.exists(path):
                raise BackupError, "sqlite database [%s] doesn't exist." % path
            total_size += os.path.getsize(path)
        return total_size

    def backup(self):
        """
        Use the internal '.dump' functionality built into SQLite to dump the 
        pure ASCII SQL Text and write that to disk.
        """
        zopts = (self.config['compression']['method'], 
                 int(self.config['compression']['level']))
        LOG.info("SQLite binary is [%s]" % self.config['sqlite']['binary'])         
        
        for db in self.config['sqlite']['databases']:
            path = os.path.abspath(os.path.expanduser(db))
            LOG.info("Backing up SQLite database at [%s]" % path)
            dest = os.path.join(self.target_directory, '%s.tar' % \
                                os.path.basename(path))                    
            dest = open_stream(dest, 'w', *zopts)
            cmd = "%s %s" % (self.config['sqlite']['binary'], 
                                            path)
            res = Popen(cmd.split(), stdin=PIPE, stdout=PIPE)
            
            # trigger sqlite to dump its data
            res.stdin.write(".dump\n")
            stdout, stderr = res.communicate()
            if stderr:
                raise BackupError, "SQLite Backup Error: %s" % stderror
            dest.write(stdout)
            dest.close()
        
