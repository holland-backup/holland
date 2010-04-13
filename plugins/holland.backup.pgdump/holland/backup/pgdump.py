"""
Plugin for the Holland backup framework
to backup Postgres databases using pg_dump
and pg_dumpall
"""

import os
import subprocess
import tempfile
import shutil
import logging

from holland.lib.mysql.client import MySQLClient
from holland.lib.mysql.find import MySQLFind
from holland.lib.mysql.config import make_mycnf
from holland.core.util.path import format_bytes, disk_free
from holland.lib.which import which, WhichError

LOGGER = logging.getLogger(__name__)

# We validate our config against the following spec
CONFIGSPEC = """
[pgdump]
data-only           = boolean(default=False)
schema-only         = boolean(default=False)
blobs               = boolean(default=False)

clean               = boolean(default=None)
create              = boolean(default=None)
inserts             = boolean(default=None)
attribute-inserts   = boolean(default=None)
oids                = boolean(default=None)

no-owner            = string(default=None)
role                = string(default=None)

schema              = string(default=None)
tables              = coerced_list(default=None)
exclude-tables      = coerced_list(default=None)

format              = option('plain','tar','custom', default='custom')
compress            = integer(min=0,max=9,default=None)

encoding            = string(default=None)
disable-dollar-quoting = boolean(default=False)

# Deprecated in 8.4(?)
ignore-version      = boolean(default=None)
lock-wait-timeout   = string(default=None)
no-tablespaces      = boolean(default=False)
verbose             = boolean(default=None)

[postgres:auth:global]
username = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(min=0,default=5432)
[postgres:auth]
username = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(default=5432)

""".splitlines()

# Used for our surrogate connection
CLIENT_TIMEOUT = 28800

class PgDump(object):
    """
    Postgres pg_dump* backups
    """
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.config.validate_config(CONFIGSPEC)
        
    def estimate_backup_size(self):
        return 0
        
    def backup(self):
        """
        Start a backup.
        """
        # First run a pg_dumpall -g and save the globals
        # Then run a pg_dump for each database we find
        pass
            
    def cleanup(self):
        """
        Finish a backup.
        
        This module does not have a cleanup phase
        """
        # No cleanup necessary
        pass
