"""
Backup plugin wrapping Percona's xtrabackup

http://www.percona.com/docs/wiki/percona-xtrabackup:innobackupex
"""

import logging

LOGGER = logging.getLogger(__name__)

CONFIGSPEC = """
[xtrabackup]
stream      = option('tar', default='tar')
sleep       = integer(min=0)
## Not supported in xtrabackup?
#compress    = integer(min=0,max=9, default=1)
#include     = string(default=None)
#uncompress  = boolean(default=None)

[mysql:client]
user        = string(default=None)
password    = string(default=None)
port        = integer(min=0, default=None)
socket      = string(default=None)
"""

class XtraBackup(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        LOGGER.info("initializing")
        if dry_run:
            LOGGER.info("dry-run mode")

    def estimate_backup_size(self):
        return 0

    def backup(self):
        """
        Do what is necessary to perform and validate a successful backup.
        """
        LOGGER.info("this plugin does nothing")

    def cleanup(self):
        """
        Cleanup from backup stage
        """
        LOGGER.info("nothing to cleanup")
