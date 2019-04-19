"""SQLite backup plugin for Holland."""

import os
import logging
from subprocess import Popen, PIPE

from holland.lib.compression import open_stream, COMPRESSION_CONFIG_STRING
from holland.core.backup import BackupError

LOG = logging.getLogger(__name__)

CONFIGSPEC = (
    """
[sqlite]
databases = force_list(default=list())
binary = string(default=/usr/bin/sqlite3)
"""
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


class SQLitePlugin(object):
    """Define Plugin to backup SQLite"""

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

        self.sqlite_bin = self.config["sqlite"]["binary"]
        self.check()

    @staticmethod
    def info():
        """??"""
        return "SQLite backup plugin for Holland."

    def check(self):
        """Check if we can take a backup"""
        LOG.info("Checking that SQLite backups can run.")
        if not os.path.exists(self.sqlite_bin):
            raise BackupError("SQLite binary [%s] doesn't exist!" % self.sqlite_bin)

        for database in self.config["sqlite"]["databases"]:
            # sometimes picks up empty string ('')
            if not database:
                continue

            path = os.path.abspath(os.path.expanduser(database))
            if not os.path.exists(path):
                LOG.error("SQLite database [%s] doesn't exist!", path)
                self.invalid_databases.append(database)
                continue

            process = Popen(
                [self.sqlite_bin, path, ".schema"],
                stdin=open("/dev/null", "r"),
                stdout=open("/dev/null", "w"),
                stderr=PIPE,
            )
            _, stderroutput = process.communicate()

            if process.returncode != 0:
                LOG.error(stderroutput)
                self.invalid_databases.append(database)
            else:
                self.databases.append(database)

        if not self.databases and not self.invalid_databases:
            raise BackupError("No SQLite databases to backup!")

    def estimate_backup_size(self):
        """
        Return total estimated size of all databases we are backing up (does
        not account for post-compression).
        """
        total_size = 0
        for database in self.databases:
            if database in self.invalid_databases:
                continue
            path = os.path.abspath(os.path.expanduser(database))
            total_size += os.path.getsize(path)
        return total_size

    def backup(self):
        """
        Use the internal '.dump' functionality built into SQLite to dump the
        pure ASCII SQL Text and write that to disk.
        """

        LOG.info("SQLite binary is [%s]", self.sqlite_bin)
        for database in self.databases:
            path = os.path.abspath(os.path.expanduser(database))

            if database in self.invalid_databases:
                LOG.warning("Skipping invalid SQLite database at [%s]", path)
                continue

            if self.dry_run:
                LOG.info("Backing up SQLite database at [%s] (dry run)", path)
                dest = open("/dev/null", "w")
            else:
                LOG.info("Backing up SQLite database at [%s]", path)
                dest = os.path.join(self.target_directory, "%s.sql" % os.path.basename(path))
                dest = open_stream(dest, "w", **self.config["compression"])

            process = Popen(
                [self.sqlite_bin, path, ".dump"],
                stdin=open("/dev/null", "r"),
                stdout=dest,
                stderr=PIPE,
            )
            _, stderroutput = process.communicate()
            dest.close()

            if process.returncode != 0:
                LOG.error(stderroutput)
                raise BackupError("SQLite '.dump' of [%s] failed" % path)

        # Raise for invalid databases after we successfully backup the others
        if self.invalid_databases:
            raise BackupError("Invalid database(s): %s" % self.invalid_databases)
