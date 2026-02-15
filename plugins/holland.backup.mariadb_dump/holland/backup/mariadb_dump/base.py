"""Main driver"""

import errno
import json
import logging

from holland.backup.mariadb_dump.command import ALL_DATABASES
from holland.core.backup import BackupError
from holland.lib.common.safefilename import encode

LOG = logging.getLogger(__name__)


def start(
    mariadb_dump,
    schema=None,
    lock_method="auto-detect",
    file_per_database=True,
    open_stream=open,
    compression_ext="",
    arg_per_database=None,
):
    """Start a mariadb-dump backup"""
    if not schema and file_per_database:
        raise BackupError("file_per_database specified without a valid schema")

    if not schema:
        target_databases = ALL_DATABASES
    else:

        if not schema.databases:
            raise BackupError("No databases found to backup")

        if not file_per_database and not list(schema.excluded_databases):
            target_databases = ALL_DATABASES
        else:
            target_databases = [db for db in schema.databases if not db.excluded]
            write_manifest(schema, open_stream, compression_ext)

    if file_per_database:
        arg_per_database = json.loads(arg_per_database) if arg_per_database else {}
        flush_logs = "--flush-logs" in mariadb_dump.options
        if flush_logs:
            mariadb_dump.options.remove("--flush-logs")
        for target_db in target_databases:
            additional_options = [mariadb_dump_lock_option(lock_method, [target_db])]
            # add --flush-logs only to the last database
            if flush_logs and target_db == target_databases[-1]:
                additional_options.append("--flush-logs")
            db_name = encode(target_db.name)
            if db_name != target_db.name:
                LOG.warning(
                    "Encoding file-name for database %s to %s", target_db.name, db_name
                )

            if db_name in arg_per_database:
                additional_options.append(arg_per_database[db_name])
            run_mariadb_dump(
                mariadb_dump,
                open_stream,
                f"{db_name}.sql",
                compression_ext,
                [target_db.name],
                additional_options,
            )
    else:
        additional_options = [mariadb_dump_lock_option(lock_method, target_databases)]
        if target_databases is not ALL_DATABASES:
            target_databases = [db.name for db in target_databases]
        run_mariadb_dump(
            mariadb_dump,
            open_stream,
            "all_databases.sql",
            compression_ext,
            target_databases,
            additional_options,
        )


def run_mariadb_dump(
    mariadb_dump, open_stream, filename, compression_ext, databases, additional_options
):
    """Run a mariadb-dump backup"""
    try:
        stream = open_stream(filename, "w")
    except (IOError, OSError) as exc:
        raise BackupError(
            "Failed to open output stream %s: %s" % (filename + compression_ext, exc)
        )
    try:
        mariadb_dump.run(databases, stream, additional_options=additional_options)
    finally:
        try:
            stream.close()
        except (IOError, OSError) as exc:
            if exc.errno != errno.EPIPE:
                LOG.error("%s", str(exc))
                raise BackupError(str(exc))


def write_manifest(schema, open_stream, ext):
    """Write real database names => encoded names to MANIFEST.txt"""
    manifest_fileobj = open_stream("MANIFEST.txt", "w", method="none")

    try:
        for database in schema.databases:
            if database.excluded:
                continue
            name = database.name
            encoded_name = encode(name)
            line = "%s %s\n" % (name, encoded_name + ".sql" + ext)
            manifest_fileobj.write(line)
    finally:
        manifest_fileobj.close()
        LOG.info("Wrote backup manifest %s", manifest_fileobj.name)


def mariadb_dump_lock_option(lock_method, databases):
    """Choose the mariadb-dump option to use for locking
    given the requested lock-method and the set of databases to
    be backed up
    """
    if lock_method == "auto-detect":
        return mariadb_dump_autodetect_lock(databases)

    valid_methods = {
        "flush-lock": "--lock-all-tables",
        "lock-tables": "--lock-tables",
        "single-transaction": "--single-transaction",
        "none": "--skip-lock-tables",
    }
    try:
        return valid_methods[lock_method]
    except KeyError:
        raise BackupError("Invalid mariadb-dump lock method %r" % lock_method)


def mariadb_dump_autodetect_lock(databases):
    """Auto-detect if we can do a transactional or
    non-transactional backup with mariadb-dump
    """

    if databases == ALL_DATABASES:
        return "--lock-all-tables"

    for database in databases:
        if database.excluded:
            continue
        for table in database.tables:
            if table.excluded:
                continue
            if not table.is_transactional:
                return "--lock-tables"

    return "--single-transaction"
