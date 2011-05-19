"""holland.backup.mysqldump interface"""

import os, sys
import logging
from holland.core import BackupError, BackupPlugin, Configspec
from holland.backup.mysqldump.mock import MockEnvironment
from holland.backup.mysqldump.util import *
from holland.backup.mysqldump.runner import MySQLBackup
from holland.backup.mysqldump.spec import CONFIGSPEC

LOG = logging.getLogger(__name__)

class MySQLDumpPlugin(BackupPlugin):
    """Backup Plugin for MySQL using mysqldump"""

    #: internal schema object where the mysqldump plugin tracks and caches
    #: metadata about tables for a MySQL instance
    _schema = None

    #: A cached MySQLClient instance used for retrieving basic information
    #: from a MySQL instance including metadata, replication info, etc.
    _client = None

    def pre(self):
        """Setup objects shared by estimate() and backup/dryrun()"""
        self._schema = schema_from_config(self.config['mysqldump'])
        self._client = client_from_config(self.config['mysql:client'])
        try:
            self._client.connect()
            LOG.info(" + Connected to MySQL")
        except MySQLError, exc:
            LOG.error(" + Connection to MySQL failed")
            raise BackupError("[%d] %s" % exc.args)
        log_host_info(self._client)
        try:
            LOG.info(" + Evaluating schema")
            refresh_schema(self._schema, self._client)
        except MySQLError, exc:
            raise BackupError("[%d] %s" % exc.args)

    def estimate(self):
        """Estimate the size of a mysqldump from MySQL metadata

        :returns: estimated size in integer number of bytes
        """
        LOG.info("Estimating backup size")
        LOG.info("----------------------")
        if self.config['mysqldump']['estimate-method'].startswith('const:'):
            return parse_size(self.config['mysqldump']['estimate-method'])
        return sum([db.size for db in self._schema.databases])

    def _setup(self):
        """Perform various setup bookkeeping"""
        os.makedirs(os.path.join(self.backup_directory, 'backup_data'))
        LOG.info("+ mkdir %s", os.path.join(self.backup_directory,
                                            'backup_data'))
        defaults_file = defaults_from_config(self.config['mysql:client'],
                                             self.backup_directory)
        LOG.info("+ mkconfig %s", defaults_file)
        write_exclusions(defaults_file, self._schema)
        LOG.info("+ exclusions >> %s", defaults_file)
        mysqld_version = server_version(self._client)
        argv = argv_from_config(defaults_file, self.config, mysqld_version)
        dotsql_generator = sql_open(os.path.join(self.backup_directory,
                                                 'backup_data'),
                                    self.config['compression'])
        lock_method = lock_method_from_config(self.config)
        if lock_method:
            LOG.info("+ lock-method forced : %s", lock_method)
        return MySQLBackup(argv, dotsql_generator, lock_method)

    def backup(self, dry_run=False):
        """Backup via mysqldump"""
        LOG.info("mysqldump backup")
        LOG.info("----------------")
        LOG.info(":databases: %s",
                 ','.join([db.name + (db.excluded and '(excluded)' or '')
                          for db in self._schema.databases]))
        try:
            try:
                backup = self._setup()
                config = self.config['mysqldump']
                if config['stop-slave']:
                    status = stop_slave(self._client)
                    record_slave_status(status, self.config)
                if config['lockless-only']:
                    check_transactional(self._schema.databases)
                if config['file-per-database']:
                    parallelism = config['parallelism']
                    explicit_tables = config['explicit-tables']
                    LOG.info("+ file-per-database")
                    LOG.info("+ parallelism=%d", parallelism)
                    generate_manifest(self.backup_directory,
                                      self._schema,
                                      self.config)
                    backup.run_each(self._schema.databases,
                                    explicit_tables=explicit_tables,
                                    parallelism=parallelism)
                else:
                    backup.run_all(self._schema.databases)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                LOG.debug("Failure(exception)", exc_info=True)
                raise BackupError("Backup failed", sys.exc_info()[1])
        finally:
            if self.config['mysqldump']['stop-slave']:
                start_slave(self._client)

    def dryrun(self):
        """Perform a dryrun backup"""
        mockenv = MockEnvironment()
        mockenv.replace_environment()
        try:
            self.backup(dry_run=True)
        finally:
            mockenv.restore_environment()

    def configspec(self):
        """Generate the configspec for the mysqldump plugin"""
        return Configspec.from_string(CONFIGSPEC)

    def plugin_info(self):
        """Provide information about this plugin"""
        return dict(
            name='mysqldump',
            summary='Backup MySQL databases via the mysqldump command',
            description='''
            ''',
            version='1.1.0a1',
            api_version='1.1.0a1',
        )
