"""SQLite backup plugin for Holland."""

import os
import logging
from subprocess import Popen, PIPE

from holland.lib.compression import open_stream
from holland.core.backup import BackupError

LOG = logging.getLogger(__name__)

CONFIGSPEC="""
[sqlite]
databases = force_list(default=list())
binary = string(default=/usr/bin/sqlite3)

[compression]
method = option('none', 'gzip', 'gzip-rsyncable', 'pigz', 'bzip2', 'pbzip2', 'lzop', default='gzip')
inline = boolean(default=yes)
level = integer(min=0, max=9, default=1)
""".splitlines()

class SQLitePlugin(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.invalid_databases = []
        self.databases = []
        
        LOG.info("Validating config: %s", self.name)
        self.config.validate_config(CONFIGSPEC)
        LOG.debug("Validated config: %r", self.config)
        
        self.sqlite_bin = self.config['sqlite']['binary']
        self.check()
        
    def info(self):
        return "SQLite backup plugin for Holland."
        
    def check(self):
        LOG.info("Checking that SQLite backups can run.")
        if not os.path.exists(self.sqlite_bin):
            raise BackupError("SQLite binary [%s] doesn't exist!" % self.sqlite_bin)    
                
        for db in self.config['sqlite']['databases']:
            # sometimes picks up empty string ('')
            if not db:
                continue
                
            path = os.path.abspath(os.path.expanduser(db))
            if not os.path.exists(path):
                LOG.error("SQLite database [%s] doesn't exist!" % path)
                self.invalid_databases.append(db)
                continue
            
            process = Popen([self.sqlite_bin, path, '.schema'], 
                            stdin=open('/dev/null', 'r'), 
                            stdout=open('/dev/null', 'w'), 
                            stderr=PIPE)
            _, stderroutput = process.communicate()
            
            if process.returncode != 0:
                LOG.error(stderroutput)
                self.invalid_databases.append(db)
            else:
                self.databases.append(db)

        if len(self.databases) == 0 and len(self.invalid_databases) == 0:
            raise BackupError("No SQLite databases to backup!")
            
    def estimate_backup_size(self):
        """
        Return total estimated size of all databases we are backing up (does 
        not account for post-compression).
        """
        total_size = 0
        for db in self.databases:
            if db in self.invalid_databases:
                continue
            path = os.path.abspath(os.path.expanduser(db))
            total_size += os.path.getsize(path)
        return total_size

    def backup(self):
        """
        Use the internal '.dump' functionality built into SQLite to dump the 
        pure ASCII SQL Text and write that to disk.
        """
        
        zopts = (self.config['compression']['method'], 
                 int(self.config['compression']['level']))
        LOG.info("SQLite binary is [%s]" % self.sqlite_bin)         
        for db in self.databases:
            path = os.path.abspath(os.path.expanduser(db))
            
            if db in self.invalid_databases:
                LOG.warn("Skipping invalid SQLite database at [%s]" % path)
                continue
            
            if self.dry_run:
                LOG.info("Backing up SQLite database at [%s] (dry run)" % path)
                dest = open('/dev/null', 'w')
            else:
                LOG.info("Backing up SQLite database at [%s]" % path)
                dest = os.path.join(self.target_directory, '%s.sql' % \
                                    os.path.basename(path))                    
                dest = open_stream(dest, 'w', *zopts)
                
            process = Popen([self.sqlite_bin, path, '.dump'], 
                            stdin=open('/dev/null', 'r'), stdout=dest, 
                            stderr=PIPE)
            _, stderroutput = process.communicate()
            dest.close()

            if process.returncode != 0:
              LOG.error(stderroutput)
              raise BackupError("SQLite '.dump' of [%s] failed" % path)

        # Raise for invalid databases after we successfully backup the others
        if len(self.invalid_databases) > 0:
            raise BackupError("Invalid database(s): %s" % self.invalid_databases)
            
