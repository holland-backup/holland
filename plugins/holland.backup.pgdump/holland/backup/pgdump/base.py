# -*- coding: utf-8 -*-
"""Backup functions for pg_dump"""


import logging

# Python stdlib
import os
import shlex
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

# holland-common safefilename encoding
from holland.lib.common.safefilename import encode as encode_safe

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

    if config["pgdump"]["role"]:
        try:
            cursor = connection.cursor()
            cursor.execute("SET ROLE %s" % config["pgdump"]["role"])
        except:
            raise BackupError("Failed to set role to " + config["pgdump"]["role"])

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


def run_pgdump(dbname, output_stream, connection_params, out_format="custom", env=None):
    """Run pg_dump for the given database and write to the specified output
    stream.

    :param db: database name
    :type db: str
    :param output_stream: a file-like object - must have a fileno attribute
                          that is a real, open file descriptor
    """
    args = ["pg_dump"] + connection_params + ["--format", out_format, dbname]

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
    be captured by pg_dump.

    Runs pg_dumpall -g > $backup_dir/globals.sql

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
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
        raise BackupError("pg_dumpall command exited with failure code %d." % returncode)


def generate_manifest(backups, path):
    """ Prints the database manifest file """
    manifest = open(os.path.join(path, "MANIFEST"), "w")
    for dbname, dumpfile in backups:
        try:
            print(
                "%s\t%s" % (dbname.encode("utf8"), os.path.basename(dumpfile)),
                file=manifest,
            )
        except UnicodeError as exc:
            LOG.error("Failed to encode dbname %s: %s", dbname, exc)
    manifest.close()


def pgauth2args(config):
    """ Returns authentication options as cli arguments """
    args = []
    remap = {"hostname": "host"}
    for param in ("hostname", "port", "username"):
        value = config["pgauth"].get(param)
        key = remap.get(param, param)
        if value is not None:
            args.extend(["--%s" % key, str(value)])

    if config["pgdump"]["role"]:
        if VER >= "8.4":
            args.extend(["--role", config["pgdump"]["role"]])
        else:
            raise BackupError(
                "The --role option is available only in Postgres versions 8.4 and higher."
            )

    return args


def pg_extra_options(config):
    """ Returns extra cli options based on pgdump config """
    args = []
    # normal compression doesn't make sense with --format=custom
    # use pg_dump's builtin --compress option instead
    if config["pgdump"]["format"] == "custom":
        LOG.info("Ignore compression method, since custom format is in use.")
        config["compression"]["method"] = "none"
        args += ["--compress", str(config["compression"]["level"])]
    additional_options = config["pgdump"]["additional-options"]
    if additional_options:
        args += shlex.split(additional_options)
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


def backup_pgsql(backup_directory, config, databases):
    """Backup databases in a Postgres instance

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
    :raises: OSError, BackupError on error
    """
    connection_params = pgauth2args(config)
    extra_options = pg_extra_options(config)

    pgenv = dict(os.environ)

    if config["pgauth"]["password"] is not None:
        pgpass_file = generate_pgpassfile(backup_directory, config["pgauth"]["password"])
        if "PGPASSFILE" in pgenv:
            LOG.warning(
                "Overriding PGPASSFILE in environment with %s because a password is specified.",
                pgpass_file,
            )
        pgenv["PGPASSFILE"] = pgpass_file

    backup_globals(backup_directory, config, connection_params, env=pgenv)

    ext_map = {"custom": ".dump", "plain": ".sql", "tar": ".tar"}

    backups = []
    for dbname in databases:
        out_format = config["pgdump"]["format"]

        dump_name = encode_safe(dbname)
        if dump_name != dbname:
            LOG.warning("Encoded database %s as filename %s", dbname, dump_name)

        filename = os.path.join(backup_directory, dump_name + ext_map[out_format])

        stream = open_stream(filename, "w", **config["compression"])
        backups.append((dbname, stream.name))

        run_pgdump(
            dbname=dbname,
            output_stream=stream,
            connection_params=connection_params + extra_options,
            out_format=out_format,
            env=pgenv,
        )

        stream.close()

    generate_manifest(backups, backup_directory)


def dry_run(databases, config):
    """ Logs what pg_dump command would be run """
    args = pgauth2args(config)

    LOG.info("pg_dumpall -g")
    for database in databases:
        LOG.info(
            "pg_dump %s --format %s %s",
            subprocess.list2cmdline(args),
            config["pgdump"]["format"],
            database,
        )
