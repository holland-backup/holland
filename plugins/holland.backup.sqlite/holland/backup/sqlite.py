"""SQLite backup plugin for Holland."""

import os
import logging
from subprocess import Popen, PIPE

from holland.core import BackupPlugin, BackupError, Configspec, open_stream

LOG = logging.getLogger(__name__)

CONFIGSPEC = """
[sqlite]
databases = force_list(default=list())
binary = string(default="/usr/bin/sqlite3")

[compression]
method = option('none', 'gzip', 'pigz', 'bzip2', 'lzop', default='gzip')
inline = boolean(default=yes)
level = integer(min=0, max=9, default=1)
"""

class SQLitePlugin(BackupPlugin):
    """
    Holland plugin to backup SQLite database files.
    """
    def __init__(self, name):
        self.name = name
        self.config = None
        self.store = None
        self.dry_run_only = False
        self.invalid_databases = []
        self.databases = []

    def pre(self):
        """
        Pre backup actions.  Primarily, ensuring that all databases are 
        valid for backup.
        """
        LOG.info("Checking that SQLite backups can run.")
        if not os.path.exists(self.config['sqlite']['binary']):
            raise BackupError, \
                "SQLite binary [%s] doesn't exist!" % \
                self.config['sqlite']['binary']

        for database in self.config['sqlite']['databases']:
            # sometimes picks up empty string ('')
            if not database:
                continue

            path = os.path.abspath(os.path.expanduser(database))
            if not os.path.exists(path):
                LOG.error("SQLite database [%s] doesn't exist!" % path)
                self.invalid_databases.append(database)
                continue

            process = Popen([self.config['sqlite']['binary'], path, '.schema'],
                            stdin=open('/dev/null', 'r'),
                            stdout=open('/dev/null', 'w'),
                            stderr=PIPE)
            _, stderroutput = process.communicate()

            if process.returncode != 0:
                LOG.error(stderroutput)
                self.invalid_databases.append(database)
            else:
                self.databases.append(database)

        if len(self.databases) == 0 and len(self.invalid_databases) == 0:
            raise BackupError, "No SQLite databases to backup!"

    def estimate(self):
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

        zopts = (self.config['compression']['method'],
                 int(self.config['compression']['level']))
        LOG.info("SQLite binary is [%s]" % self.config['sqlite']['binary'])
        for database in self.databases:
            path = os.path.abspath(os.path.expanduser(database))

            if database in self.invalid_databases:
                LOG.warn("Skipping invalid SQLite database at [%s]" % path)
                continue

            if self.dry_run_only:
                LOG.info("Backing up SQLite database at [%s] (dry run)" % \
                         path)
                dest = open('/dev/null', 'w')
            else:
                LOG.info("Backing up SQLite database at [%s]" % path)
                dest = os.path.join(self.store.path, '%s.sql' % \
                                    os.path.basename(path))
                try:
                    dest = open_stream(dest, 'w', *zopts)
                except IOError, error:
                    raise BackupError, "SQLite IOError %s %s" \
                        % (error.args[1], dest)     
                
            process = Popen([self.config['sqlite']['binary'], path, '.dump'],
                            stdin=open('/dev/null', 'r'), stdout=dest,
                            stderr=PIPE)
            _, stderroutput = process.communicate()
            dest.close()

            if process.returncode != 0:
                LOG.error(stderroutput)
                raise BackupError("SQLite '.dump' of [%s] failed" % path)

        # Raise for invalid databases after we successfully backup the others
        if len(self.invalid_databases) > 0:
            raise BackupError, "Invalid database(s): %s" % \
                                self.invalid_databases

    def dryrun(self):
        """
        Do mostly everyting, but use /dev/null for databses.
        """
        self.dry_run_only = True
        self.backup()

    def configspec(self):
        """Configspec that the sqlite plugin accepts"""
        return Configspec.from_string(CONFIGSPEC)

    def plugin_info(self):
        """Sqlite Plugin Metadata"""
        return dict(
                name='sqlite',
                summary='Backup SQLite Files',
                description='''
                ''',
                version='1.1.0a1',
                api_version='1.1.0a1',
        )
