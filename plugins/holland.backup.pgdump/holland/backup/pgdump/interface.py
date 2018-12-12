# -*- coding: utf-8 -*-
"""
Plugin for the Holland backup framework
to backup Postgres databases using pg_dump
and pg_dumpall
"""

import os
import logging
from holland.core.backup import BackupError
from holland.backup.pgdump.base import dry_run as pg_dry_run
from holland.backup.pgdump.base import backup_pgsql, \
                                       PgError, \
                                       dbapi, \
                                       pg_databases, \
                                       get_connection, get_db_size, \
                                       legacy_get_db_size
from holland.lib.compression import COMPRESSION_CONFIG_STRING

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
additional-options = string(default=None)

[pgauth]
username = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(default=None)
""" + COMPRESSION_CONFIG_STRING

CONFIGSPEC = CONFIGSPEC.splitlines()


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

        self.connection = get_connection(self.config)
        self.databases = pg_databases(self.config, self.connection)
        LOG.info("Found databases: %s", ','.join(self.databases))

    def estimate_backup_size(self):
        """Estimate the size (in bytes) of the backup this plugin would
        produce, if run.


        :returns: int. size in bytes
        """

        totalestimate = 0
        for database in self.databases:
            try:
                totalestimate += get_db_size(database, self.connection)
            except dbapi.DatabaseError as exc:
                if exc.pgcode != '42883': # 'missing function'
                    raise BackupError("Failed to estimate database size for "
                                      "%s: %s" % (database, exc))
                totalestimate += self._estimate_legacy_size(database)

        return totalestimate

    def _estimate_legacy_size(self, database):
        try:
            connection = get_connection(self.config, database)
            size = legacy_get_db_size(database, connection)
            connection.close()
            return size
        except dbapi.DatabaseError as exc:
            raise BackupError("Failed to estimate database size for %s: %s" %
                              (database, exc))

    def backup(self):
        """
        Start a backup.
        """

        # estimate and setup has completed at this point
        # so ensure the connection is closed - we will never reuse this
        self.connection.close()

        if self.dry_run:
            # Very simply dry run information
            # enough to know that:
            # 1) We can connect to Postgres using pgpass data
            # 2) The exact databases we would dump
            pg_dry_run(self.databases, self.config)
            return

        # First run a pg_dumpall -g and save the globals
        # Then run a pg_dump for each database we find
        backup_dir = os.path.join(self.target_directory, 'data')

        # put everything in data/
        try:
            os.mkdir(backup_dir)
        except OSError as exc:
            raise BackupError("Failed to create backup directory %s" % backup_dir)

        try:
            backup_pgsql(backup_dir, self.config, self.databases)
        except (OSError, PgError) as exc:
            LOG.debug("Failed to backup Postgres. %s",
                      str(exc), exc_info=True)
            raise BackupError(str(exc))

    @classmethod
    def configspec(cls):
        """Provide a specification for the configuration dictionary this
        plugin accepts.
        """
        return CONFIGSPEC

    def info(self):
        """Provide extra information about a backup

        :returns: str. Descriptive text about the backup
        """

        return str(self.config)
