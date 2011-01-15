"""holland.backup.mysqldump interface"""

import os, sys
import logging
from holland.core import BackupError
from holland.backup.mysqldump.mock import MockEnvironment
from holland.backup.mysqldump.util import *
from holland.backup.mysqldump.runner import MySQLBackup
from holland.backup.mysqldump.spec import CONFIGSPEC

LOG = logging.getLogger(__name__)

class MySQLDumpPlugin(object):
    name = 'mysqldump'

    def __init__(self, backupstore):
        self.backupstore = backupstore
        self.path = self.backupstore.path
        self.config = None

    def configure(self, config):
        config.validate_config(CONFIGSPEC)
        self.config = config

    def setup(self):
        self._schema = schema_from_config(self.config['mysqldump'])
        self._client = client_from_config(self.config['mysql:client'])

    def estimate(self):
        LOG.info("Estimating backup size")
        LOG.info("----------------------")
        if self.config['mysqldump']['estimate-method'].startswith('const:'):
            return parse_size(self.config['mysqldump']['estimate-method'])

        refresh_schema(self._schema, self._client)

        return sum([db.size for db in self._schema.databases])

    def _setup(self):
        os.makedirs(os.path.join(self.path, 'backup_data'))
        LOG.info("+ mkdir %s", os.path.join(self.path, 'backup_data'))
        defaults_file = defaults_from_config(self.config['mysql:client'],
                                             self.path)
        LOG.info("+ mkconfig %s", defaults_file)
        write_exclusions(defaults_file, self._schema)
        LOG.info("+ exclusions >> %s", defaults_file)
        mysqld_version = server_version(self._client)
        argv = argv_from_config(defaults_file, self.config, mysqld_version)
        dotsql_generator = sql_open(self.path,
                                    self.config['compression'])
        lock_method = lock_method_from_config(self.config)
        if lock_method:
            LOG.info("+ lock-method forced : %s", lock_method)
        return MySQLBackup(argv, dotsql_generator, lock_method)

    def backup(self, dry_run=False):
        LOG.info("mysqldump backup")
        LOG.info("----------------")
        LOG.info(":databases: %s",
                 ','.join([db.name for db in self._schema.databases]))
        if dry_run:
            mockenv = MockEnvironment()
            mockenv.replace_environment()
        try:
            try:
                backup = self._setup()
                if self.config['mysqldump']['stop-slave']:
                    status = stop_slave(self._client)
                    record_slave_status(self.config)
                if self.config['mysqldump']['file-per-database']:
                    parallelism = self.config['mysqldump']['parallelism']
                    LOG.info("+ file-per-database")
                    LOG.info("+ parallelism=%d", parallelism)
                    generate_manifest(self.path, self._schema, self.config)
                    backup.run_each(self._schema.databases, parallelism)
                else:
                    backup.run_all(self._schema.database)
            except:
                LOG.exception("Failure")
                raise BackupError("Backup failed", sys.exc_info()[1])
        finally:
            if dry_run:
                mockenv.restore_environment()
            if self.config['mysqldump']['stop-slave']:
                start_slave(self._client)

    def teardown(self):
        pass

    #@classmethod
    def configspec(cls):
        return CONFIGSPEC
    configspec = classmethod(configspec)

    def info(self):
        # deprecated
        return ""
