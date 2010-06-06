"""Main driver"""

import csv
import logging
from holland.core.exceptions import BackupError
from holland.lib.safefilename import encode
from holland.backup.mysqldump.command import ALL_DATABASES
from holland.backup.mysqldump.mock.env import MockEnvironment

LOG = logging.getLogger(__name__)

def dry_run(*args, **kwargs):
    """Run a backup in no-op mode"""
    env = MockEnvironment()
    try:
        env.replace_environment()
        start(*args, **kwargs)
    finally:
        env.restore_environment()

def run(mysqldump, config): pass

def start(mysqldump,
          schema=None,
          lock_method='auto-detect',
          file_per_database=True,
          open_stream=open):
    """Run a mysqldump backup"""

    if not schema and file_per_database:
        raise BackupError("file_per_database specified without a valid schema")

    if not schema:
        target_databases = ALL_DATABASES
    else:

        if not file_per_database and not [x for x in schema.excluded_databases]:
            target_databases = ALL_DATABASES
        else:
            target_databases = [db for db in schema.databases
                                    if not db.excluded]
            write_manifest(schema, open_stream)

    if file_per_database:
        flush_logs = '--flush-logs' in mysqldump.options
        if flush_logs:
            mysqldump.options.remove('--flush-logs')
        last = len(target_databases)
        for count, db in enumerate(target_databases):
            more_options = [mysqldump_lock_option(lock_method, [db])]
            # add --flush-logs only to the last mysqldump run
            if flush_logs and count == last:
                more_options.append('--flush-logs')
            db_name = encode(db.name)[0]
            if db_name != db.name:
                LOG.warning("Encoding file-name for database %s to %s", db.name, db_name)
            stream = open_stream('%s.sql' % db_name, 'w')
            mysqldump.run([db.name], stream, more_options)
    else:
        more_options = [mysqldump_lock_option(lock_method, target_databases)]
        stream = open_stream('all_databases.sql', 'w')
        if target_databases is not ALL_DATABASES:
            target_databases = [db.name for db in target_databases]
        mysqldump.run(target_databases, stream, more_options)

def write_manifest(schema, open_stream):
    """Write real database names => encoded names to MANIFEST.txt"""
    manifest_fileobj = open_stream('MANIFEST.txt', 'w', method='none')
    manifest = csv.writer(manifest_fileobj)
    for database in schema.databases:
        name = database.name
        encoded_name = encode(name)[0]
        manifest.writerow([name.encode('utf-8'), encoded_name + '.sql'])
    manifest_fileobj.close()

def mysqldump_lock_option(lock_method, databases):
    """Choose the mysqldump option to use for locking
    given the requested lock-method and the set of databases to
    be backed up
    """
    if lock_method == 'auto-detect':
        return mysqldump_autodetect_lock(databases)
    else:
        valid_methods = {
            'flush-lock'            : '--lock-all-tables',
            'lock-tables'           : '--lock-tables',
            'single-transaction'    : '--single-transaction',
            'none'                  : '--skip-lock-tables',
        }
        try:
            return valid_methods[lock_method]
        except KeyError:
            raise BackupError("Invalid mysqldump lock method %r" % \
                              lock_method)

def mysqldump_autodetect_lock(databases):
    """Auto-detect if we can do a transactional or
    non-transactional backup with mysqldump
    """

    if databases == ALL_DATABASES:
        return '--lock-all-tables'

    for database in databases:
        if database.excluded:
            continue
        for table in database.tables:
            if table.excluded:
                continue
            if not table.is_transactional:
                return '--lock-tables'
    else:
        return '--single-transaction'
