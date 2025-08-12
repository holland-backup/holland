# -*- coding: utf-8 -*-
"""Backup functions for pg_basebackup"""


import logging

# Python stdlib
import os
import subprocess
import tempfile

# 3rd party Postgres db connector
import psycopg2 as dbapi
import psycopg2.extensions

from holland.core.backup import BackupError

# holland-core has a few nice utilities such as format_bytes
from holland.core.util.fmt import format_bytes

# Holland general compression functions
from holland.lib.common.compression import open_stream
from holland.lib.common.util import parse_arguments

LOG = logging.getLogger(__name__)
VER = None


def get_connection(config, pgdb="template1"):
    """ Returns a connection to the PG database instance. """
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    args = {}
    # remap pgauth parameters to what psycopg2.connect accepts
    remap = {"hostname": "host", "username": "user"}
    for key in ("hostname", "port", "username", "password"):
        value = config["pgauth"].get(key)
        key = remap.get(key, key)
        if value is not None:
            args[key] = value
    try:
        connection = dbapi.connect(database=pgdb, **args)
    except:
        raise BackupError("Failed to connect to the Postgres database.")
    if not connection:
        raise BackupError("Failed to connect to the Postgres database.")

    # set connection in autocommit mode
    connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    global VER  # pylint: disable=W0603
    VER = connection.get_parameter_status("server_version")
    LOG.info("Server version %s", VER)

    return connection


def get_db_size(dbname, connection):
    """ Returns int -> size of the database """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT pg_database_size('%s')" % dbname)
        size = int(cursor.fetchone()[0])
        LOG.info("DB %s size %s", dbname, format_bytes(size))
        return size
    except:
        raise BackupError("Could not detmine database size.")


def legacy_get_db_size(dbname, connection):
    """ Legacy method to return db int -> size. """
    cursor = connection.cursor()
    cursor.execute("SELECT SUM(relpages*8192) FROM pg_class")
    size = int(cursor.fetchone()[0])
    LOG.info("DB %s size %s", dbname, format_bytes(size))
    cursor.close()
    return size


def pg_databases(config, connection):  # pylint: disable=W0613
    # this may be an oversight/bug by not
    # using the config param
    """Find the databases available in the Postgres cluster specified
    in config['pgpass']
    """
    cursor = connection.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE not datistemplate and datallowconn")
    databases = [db for db, in cursor]
    cursor.close()
    logging.debug("pg_databases() -> %r", databases)
    return databases


def run_pg_basebackup(output_stream, connection_params, config, directory, env=None):
    """Run pg_basebackup for the given database and write to the specified output
    stream.

    :param db: database name
    :type db: str
    :param output_stream: a file-like object - must have a fileno attribute
                          that is a real, open file descriptor
    """
    method = config["pg-basebackup"]["wal-method"]
    checkpoint = config["pg-basebackup"]["checkpoint"]
    out_format = config["pg-basebackup"]["format"]
    args = [
        "pg_basebackup",
        "-F",
        out_format,
        "-D",
        directory,
        "-X",
        method,
    ]

    if checkpoint != "none":
        args += ["-c%s" % checkpoint]
    args += connection_params

    stderr = tempfile.TemporaryFile()
    if not output_stream:
        output_stream = stderr
        LOG.info("Compression settings are ignore with format %s", out_format)
        LOG.info("%s", subprocess.list2cmdline(args))
    else:
        LOG.info("%s > %s", subprocess.list2cmdline(args), output_stream.name)
    try:
        try:
            returncode = subprocess.call(
                args, stdout=output_stream, stderr=stderr, env=env, close_fds=True
            )
        except OSError as exc:
            raise BackupError(
                "Failed to execute '%s': [%d] %s" % (args[0], exc.errno, exc.strerror)
            )

        stderr.flush()
        stderr.seek(0)
        for line in stderr:
            LOG.error("%s", line.rstrip())
    finally:
        stderr.close()
    if returncode != 0:
        raise BackupError("%s failed." % subprocess.list2cmdline(args))


def backup_globals(backup_directory, config, connection_params, env=None):
    """Backup global Postgres data that wouldn't otherwise
    be captured by pg_basebackup.

    Runs pg_backupall -g > $backup_dir/globals.sql

    :param backup_directory: directory to save pg_basebackup output to
    :param config: PgBaseBackupPlugin config dictionary
    :raises: OSError, BackupError on error
    """

    path = os.path.join(backup_directory, "global.sql")
    output_stream = open_stream(path, "w", **config["compression"])

    args = ["pg_dumpall", "-g"] + connection_params

    LOG.info("%s > %s", subprocess.list2cmdline(args), output_stream.name)
    stderr = tempfile.TemporaryFile()
    try:
        try:
            returncode = subprocess.call(
                args, stdout=output_stream, stderr=stderr, env=env, close_fds=True
            )
        except OSError as exc:
            raise BackupError(
                "Failed to execute '%s': [%d] %s" % (args[0], exc.errno, exc.strerror)
            )

        output_stream.close()
        stderr.flush()
        stderr.seek(0)
        for line in stderr:
            LOG.error("%s", line.rstrip())
    finally:
        stderr.close()

    if returncode != 0:
        raise BackupError("pg_basebackupall command exited with failure code %d." % returncode)


def pgauth2args(config):
    """ Returns authentication options as cli arguments """
    args = []
    remap = {"hostname": "host"}
    for param in ("hostname", "port", "username"):
        value = config["pgauth"].get(param)
        key = remap.get(param, param)
        if value is not None:
            args.extend(["--%s" % key, str(value)])

    return args


def generate_pgpassfile(backup_directory, password):
    """ Creates a pgpass file from a given password """
    fileobj = open(os.path.join(backup_directory, "pgpass"), "w")
    # pgpass should always be 0600
    os.chmod(fileobj.name, 0o600)
    password = password.replace("\\", "\\\\")
    password = password.replace(":", "\\:")
    fileobj.write("*:*:*:*:%s" % password)
    fileobj.close()
    return fileobj.name


def backup_pgsql(backup_directory, config):
    """Backup databases in a Postgres instance

    :param backup_directory: directory to save pg_basebackup output to
    :param config: PgBaseBackupPlugin config dictionary
    :raises: OSError, BackupError on error
    """
    connection_params = pgauth2args(config)
    extra_options = parse_arguments(
        config["pg-basebackup"]["additional-options"],
        backup_directory=backup_directory,
        backupdir=backup_directory,
    )
    out_format = config["pg-basebackup"]["format"]
    method = config["pg-basebackup"]["wal-method"]

    if out_format == "tar" and method == "stream":
        raise BackupError("The 'tar' format is not supported with the 'stream' method")

    pgenv = dict(os.environ)

    if config["pgauth"]["password"] is not None:
        pgpass_file = generate_pgpassfile(backup_directory, config["pgauth"]["password"])
        if "PGPASSFILE" in pgenv:
            LOG.warning(
                "Overriding PGPASSFILE in environment with %s because a password is specified.",
                pgpass_file,
            )
        pgenv["PGPASSFILE"] = pgpass_file

    if out_format == "tar":
        filename = os.path.join(backup_directory, "all.tar")
        stream = open_stream(filename, "w", **config["compression"])
        run_pg_basebackup(
            stream,
            connection_params + extra_options,
            config,
            "-",
            env=pgenv,
        )
        stream.close()
    elif out_format == "plain":
        run_pg_basebackup(
            None,
            connection_params + extra_options,
            config,
            backup_directory,
            env=pgenv,
        )
    else:
        raise BackupError("Unsupported format")

    backup_globals(backup_directory, config, connection_params, env=pgenv)


def dry_run(config):
    """ Logs what pg_basebackup command would be run """
    args = pgauth2args(config)
    cmd = (
        [
            "pg_basebackup",
            "-F",
            config["pg-basebackup"]["format"],
            "-D",
            "-",
            "-X",
            config["pg-basebackup"]["wal-method"],
        ]
        + args
        + config["pg-basebackup"]["additional-options"]
    )

    LOG.info("pg_dumpall -g")
    LOG.info(subprocess.list2cmdline(cmd))
