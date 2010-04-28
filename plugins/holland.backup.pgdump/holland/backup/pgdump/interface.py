"""
Plugin for the Holland backup framework
to backup Postgres databases using pg_dump
and pg_dumpall
"""

import os
import logging
from holland.backup.pgdump.base import backup_pgsql, PgError, pg_databases

LOG = logging.getLogger(__name__)

# This is a specification of what our configuration must include
# values are validate.py functions.  See:
# http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[pgdump]
data-only               = boolean(default=no)
schema-only             = boolean(default=no)
blobs                   = boolean(default=no)

clean                   = boolean(default=no)
create                  = boolean(default=no)
inserts                 = boolean(default=no)
attribute-inserts       = boolean(default=no)
oids                    = boolean(default=no)

no-owner                = boolean(default=no)

schemas                 = force_list(default=None)
exclude-schemas         = force_list(default=None)
tables                  = force_list(default=None)
exclude-tables          = force_list(default=None)

format                  = option('plain','tar','custom', default='custom')
compress                = integer(min=0,max=9,default=None)

encoding                = string(default=None)
disable-dollar-quoting  = boolean(default=no)

# Deprecated in 8.4(?)
ignore-version          = boolean(default=None)
lock-wait-timeout       = string(default=None)
no-tablespaces          = boolean(default=False)
verbose                 = boolean(default=None)

[pgauth]
username = string(default=None)
role = string(default=None)
password = string(default=None)
hostname = string(default=None)
port = integer(default=5432)
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

    def estimate_backup_size(self):
        """Estimate the size (in bytes) of the backup this plugin would
        produce, if run.


        :returns: int. size in bytes
        """
        # Here we might select the sum of pg_relation_size() (as an
        # underestimate) or pg_total_relation_size() (as an overestimate)
        # of each relation we expect tomatch with pg_dump

        # but we currently return 0
        return 0

    def backup(self):
        """
        Start a backup.
        """

        if self.dry_run:
            # Very simply dry run information
            # enough to know that:
            # 1) We can connect to Postgres using pgpass data
            # 2) The exact databases we would dump
            for name in pg_databases(self.config):
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
            backup_pgsql(backup_dir, self.config)
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
