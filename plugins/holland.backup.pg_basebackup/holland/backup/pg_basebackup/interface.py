# -*- coding: utf-8 -*-
"""
Plugin for the Holland backup framework
to backup Postgres databases using pg_basebackup
and pg_backupall
"""

import logging
import os

from holland.backup.pg_basebackup.base import backup_pgsql, dbapi
from holland.backup.pg_basebackup.base import dry_run as pg_dry_run
from holland.backup.pg_basebackup.base import (
    get_connection,
    get_db_size,
    legacy_get_db_size,
    pg_databases,
)
from holland.core.backup import BackupError
from holland.lib.compression import COMPRESSION_CONFIG_STRING

LOG = logging.getLogger(__name__)

# This is a specification of what our configuration must include
# values are validate.py functions.  See:
# http://www.voidspace.org.uk/python/validate.html

# NOTE: this configuration isn't actually obeyed by the implementation
#       These are just various options that *might* be useful for pg_basebackup
#       to support (namely database/schema/table inclusion/exclusion).
# Anyone who picks up this plugin will likely want to trim or add to this
# as it makes sense
CONFIGSPEC = (
    """
[pg-basebackup]
format = option('tar','plain',default='tar')
wal-method = option('none','fetch','stream',default='fetch')
checkpoint = option('none','fast','spread',default='fast')
additional-options = force_list(default=list())

[pgauth]
username = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(default=None)
"""
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


class PgBaseBackup(object):
    """
    Postgres pg_basebackup backups
    """

    def __init__(self, name, config, target_directory, dry_run=False):
        """Create a new PgBaseBackup instance

        :param name: unique name of this backup (e.g. pg_basebackup/20100101_000000)
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

        self.databases = None

    def estimate_backup_size(self):
        """Estimate the size (in bytes) of the backup this plugin would
        produce, if run.


        :returns: int. size in bytes
        """

        totalestimate = 0
        connection = get_connection(self.config)
        self.databases = pg_databases(self.config, connection)
        LOG.info("Found databases: %s", ",".join(self.databases))
        for database in self.databases:
            try:
                totalestimate += get_db_size(database, connection)
            except dbapi.DatabaseError as exc:
                if exc.pgcode != "42883":  # 'missing function'
                    raise BackupError(
                        "Failed to estimate database size for " "%s: %s" % (database, exc)
                    )
                totalestimate += self._estimate_legacy_size(database)
        connection.close()
        return totalestimate

    def _estimate_legacy_size(self, database):
        try:
            connection = get_connection(self.config, database)
            size = legacy_get_db_size(database, connection)
            connection.close()
            return size
        except dbapi.DatabaseError as exc:
            raise BackupError("Failed to estimate database size for %s: %s" % (database, exc))

    def backup(self):
        """
        Start a backup.
        """

        if not self.databases:
            connection = get_connection(self.config)
            self.databases = pg_databases(self.config, connection)
            LOG.info("Found databases: %s", ",".join(self.databases))
            connection.close()

        if self.dry_run:
            # Very simply dry run information
            # enough to know that:
            # 1) We can connect to Postgres using pgpass data
            # 2) The exact databases we would dump
            pg_dry_run(self.config)
            return

        backup_dir = os.path.join(self.target_directory, "data")

        # put everything in data/
        try:
            os.mkdir(backup_dir)
        except OSError:
            raise BackupError("Failed to create backup directory %s" % backup_dir)

        try:
            backup_pgsql(backup_dir, self.config)
        except (OSError, BackupError) as exc:
            LOG.debug("Failed to backup Postgres. %s", str(exc), exc_info=True)
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
