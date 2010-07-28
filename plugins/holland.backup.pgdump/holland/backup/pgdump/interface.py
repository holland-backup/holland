# -*- coding: utf-8 -*-
"""
Plugin for the Holland backup framework
to backup Postgres databases using pg_dump
and pg_dumpall
"""

import os
import sys
import logging
from tempfile import NamedTemporaryFile
from holland.backup.pgdump.base import backup_pgsql, PgError, pg_databases, get_connection, get_db_size

LOG = logging.getLogger(__name__)

# This is a specification of what our configuration must include
# values are validate.py functions.  See:
# http://www.voidspace.org.uk/python/validate.html

# NOTE: this configuration isn't actually obeyed by the implementation
#       These are just various options that *might* be useful for pg_dump
#       to support (namely database/schema/table inclusion/exclusion).
# Anyone who picks up this plugin will likely want to trim or add to this
# as it makes sense
CONFIGSPEC = """
[pgdump]
format = option('plain','tar','custom', default='custom')
role = string(default=None)

[compression]
method = option('gzip', 'bzip2', 'lzop', 'lzma', 'pigz', 'none', default='gzip')
level = integer(min=0, default=1)

[pgauth]
username = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(default=None)
pgpass = string(default=None)
""".splitlines()

class PgDump(object):
    """
    Postgres pg_dump backups
    """

    def __init__(self, name, config, target_directory, dry_run=False):
        """Create a new PgDump instance

        :param name: unique name of this backup (e.g. pg_dump/20100101_000000)
        :param target_directory: where backup files should be stored
        :param dry_run: boolean flag indicating whether we should only go
                        through the motions of a backup without actually
                        performing the heavy weight steps.
        """
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.config.validate_config(CONFIGSPEC)
        
        # We need either a pgpass or a password, at minimum
        self.pgpass = self.config["pgauth"]["pgpass"]
        if not (self.config["pgauth"]["password"] or self.pgpass):
            raise PgError("Must specify at least a password or a .pgpass file")

        if not self.pgpass:
            # write one in the target directory
            # self.pgpass = os.path.join(target_directory, "pgpass")
            self.f = NamedTemporaryFile()
            self.pgpass = self.f.name
            LOG.info("Creating pgpass " + self.pgpass)
            try:
                self.f.write(":".join((self.config["pgauth"]["hostname"], str(self.config["pgauth"]["port"]), "*",
                self.config["pgauth"]["username"], self.config["pgauth"]["password"])))
                self.f.flush()
            except IOError as e:
                LOG.info("I/O Error creating pgpass: " + str(e))

        os.environ["PGPASSFILE"] = self.pgpass

        self.connection = get_connection(self.config)
        self.databases = pg_databases(self.config, self.connection)
        LOG.info("Got databases: %s" % repr(self.databases))
        
    def estimate_backup_size(self):
        """Estimate the size (in bytes) of the backup this plugin would
        produce, if run.


        :returns: int. size in bytes
        """
        
        totalestimate = 0
        for db in self.databases:
	    totalestimate += get_db_size(db, self.connection)
	    
	return totalestimate

    def backup(self):
        """
        Start a backup.
        """

        if self.dry_run:
            # Very simply dry run information
            # enough to know that:
            # 1) We can connect to Postgres using pgpass data
            # 2) The exact databases we would dump
            for name in self.databases:
                LOG.info('pg_dump -Fc %s', name)
            return

        # First run a pg_dumpall -g and save the globals
        # Then run a pg_dump for each database we find
        backup_dir = os.path.join(self.target_directory, 'data')

        # put everything in data/
        try:
            os.mkdir(backup_dir)
        except OSError, exc:
            raise PgError("Failed to create backup directory %s" % backup_dir)

        try:
            backup_pgsql(backup_dir, self.config, self.databases)
        except OSError, exc:
            LOG.error("Failed to backup Postgres. %s",
                          str(exc), exc_info=True)
            return 1

    def configspec(cls):
        """Provide a specification for the configuration dictionary this
        plugin accepts.
        """
        return CONFIGSPEC
    configspec = classmethod(configspec)

    def info(self):
        """Provide extra information about a backup

        :returns: str. Descriptive text about the backup
        """

        return ""

#    def __del__(self):
#        if self.pgpass == "/tmp/.pgpass":
#	    os.unlink("/tmp/.pgpass")

