# -*- coding: utf-8 -*-
"""Backup functions for pg_dump"""

# Python stdlib
import os
import shlex
import tempfile
import logging
import subprocess

# 3rd party Postgres db connector
import psycopg2 as dbapi
import psycopg2.extensions

# holland-core has a few nice utilities such as format_bytes
from holland.core.util.fmt import format_bytes
# Holland general compression functions
from holland.lib.compression import open_stream
# holland-common safefilename encoding
from holland.lib.safefilename import encode as encode_safe

LOG = logging.getLogger(__name__)

class PgError(Exception):
    """Raised when any error associated with Postgres occurs"""

def get_connection(config, db='template1'):
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    args = {}
    # remap pgauth parameters to what psycopg2.connect accepts
    remap = { 'hostname' : 'host', 'username' : 'user' }
    for key in ('hostname', 'port', 'username', 'password'):
        value = config['pgauth'].get(key)
        key = remap.get(key, key)
        if value is not None:
            args[key] = value
    connection = dbapi.connect(database=db, **args)
    if not connection:
        raise PgError("Failed to connect to the Postgres database.")

    if config["pgdump"]["role"]:
        try:
            cursor = connection.cursor()
            cursor.execute("SET ROLE %s" % config["pgdump"]["role"])
        except:
            raise PgError("Failed to set role to " + config["pgdump"]["role"])

    global ver
    ver = connection.get_parameter_status('server_version')
    LOG.info("Server version " + ver)

    return connection

def get_db_size(dbname, connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT pg_database_size('%s')" % dbname)
        size = int(cursor.fetchone()[0])
        LOG.info("DB %s size %s", dbname, format_bytes(size))
        return size
    except:
        raise PgError("Could not detmine database size.")

def legacy_get_db_size(dbname, connection):
    cursor = connection.cursor()
    cursor.execute('SELECT SUM(relpages*8192) FROM pg_class')
    size = int(cursor.fetchone()[0])
    LOG.info("DB %s size %s", dbname, format_bytes(size))
    cursor.close()
    return size

def pg_databases(config, connection):
    """Find the databases available in the Postgres cluster specified
    in config['pgpass']
    """
    cursor = connection.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE not datistemplate and datallowconn")
    databases = [db for db, in cursor]
    cursor.close()
    logging.debug("pg_databases() -> %r", databases)
    return databases

def run_pgdump(dbname, output_stream, connection_params, format='custom', env=None):
    """Run pg_dump for the given database and write to the specified output
    stream.

    :param db: database name
    :type db: str
    :param output_stream: a file-like object - must have a fileno attribute
                          that is a real, open file descriptor
    """
    args = [ 'pg_dump' ] + connection_params + [
        '--format', format,
        dbname
    ]

    LOG.info('%s > %s', subprocess.list2cmdline(args),
                        output_stream.name)

    stderr = tempfile.TemporaryFile()
    returncode = subprocess.call(args,
                                 stdout=output_stream,
                                 stderr=stderr,
                                 env=env,
                                 close_fds=True)
    stderr.flush()
    stderr.seek(0)
    for line in stderr:
        LOG.error('%s', line.rstrip())
    stderr.close()

    if returncode != 0:
        raise OSError("%s failed." %
                      subprocess.list2cmdline(args))

def backup_globals(backup_directory, config, connection_params, env=None):
    """Backup global Postgres data that wouldn't otherwise
    be captured by pg_dump.

    Runs pg_dumpall -g > $backup_dir/globals.sql

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
    :raises: OSError, PgError on error
    """

    path = os.path.join(backup_directory, 'global.sql')
    output_stream = open_stream(path, 'w', **config['compression'])

    args = [
        'pg_dumpall',
        '-g',
    ] + connection_params

    LOG.info('%s > %s', subprocess.list2cmdline(args),
                        output_stream.name)
    stderr = tempfile.TemporaryFile()
    returncode = subprocess.call(args,
                                 stdout=output_stream,
                                 stderr=stderr,
                                 env=env,
                                 close_fds=True)
    output_stream.close()
    stderr.flush()
    stderr.seek(0)
    for line in stderr:
        LOG.error('%s', line.rstrip())
    stderr.close()

    if returncode != 0:
        raise PgError("pg_dumpall command exited with failure code %d." %
                      returncode)

def generate_manifest(backups, path):
    manifest = open(os.path.join(path, 'MANIFEST'), 'w')
    for dbname, dumpfile in backups:
        try:
            print >>manifest, "%s\t%s" % (dbname.encode('utf8'),
                                          os.path.basename(dumpfile))
        except UnicodeError, exc:
            LOG.error("Failed to encode dbname %s: %s", dbname, exc)
    manifest.close()

def pgauth2args(config):
    args = []
    remap = { 'hostname' : 'host' }
    for param in ('hostname', 'port', 'username'):
        value = config['pgauth'].get(param)
        key = remap.get(param, param)
        if value is not None:
            args.extend(['--%s' % key, str(value)])

    # FIXME: --role only works on 8.4+
    if config['pgdump']['role']:
        if ver >= '8.4':
            args.extend(['--role', config['pgdump']['role']])
        else:
            raise PgError("The --role option is available only in Postgres versions 8.4 and higher.")

    return args

def pg_extra_options(config):
    args = []
    # normal compression doesn't make sense with --format=custom
    # use pg_dump's builtin --compress option instead
    if config['pgdump']['format'] == 'custom':
        LOG.info("Ignore compression method, since custom format is in use.")
        config['compression']['method'] = 'none'
        args += ['--compress',
                 str(config['compression']['level'])]
    if config['pgdump']['additional-options']:
        # XXX: we may want to check these options more carefully and warn as appropriate.
        args += shlex.split(config['pgdump']['additional-options'])
    return args

def generate_pgpassfile(backup_directory, password):
    fileobj = open(os.path.join(backup_directory, 'pgpass'), 'w')
    # pgpass should always be 0600
    os.chmod(fileobj.name, 0600)
    fileobj.write('*:*:*:*:%s' % password)
    fileobj.close()
    return fileobj.name

def backup_pgsql(backup_directory, config, databases):
    """Backup databases in a Postgres instance

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
    :raises: OSError, PgError on error
    """
    connection_params = pgauth2args(config)
    extra_options = pg_extra_options(config)

    pgenv = dict(os.environ)

    if config['pgauth']['password'] is not None:
        pgpass_file = generate_pgpassfile(backup_directory,
                                          config['pgauth']['password'])
        if 'PGPASSFILE' in pgenv:
            LOG.warn("Overriding PGPASSFILE in environment with %s because "
                     "a password is specified.",
                      pgpass_file)
        pgenv['PGPASSFILE'] = pgpass_file

    backup_globals(backup_directory, config, connection_params, env=pgenv)

    ext_map = {
        'custom' : '.dump',
        'plain' : '.sql',
        'tar' : '.tar',
    }


    backups = []
    for dbname in databases:
        format = config['pgdump']['format']

        dump_name, _ = encode_safe(dbname)
        if dump_name != dbname:
            LOG.warn("Encoded database %s as filename %s", dbname, dump_name)

        filename = os.path.join(backup_directory, dump_name + ext_map[format])

        stream = open_stream(filename, 'w', **config['compression'])

        backups.append((dbname, stream.name))

        run_pgdump(dbname=dbname,
                   output_stream=stream,
                   connection_params=connection_params + extra_options,
                   format=format,
                   env=pgenv)

        stream.close()

    generate_manifest(backups, backup_directory)

def dry_run(databases, config):
    args = pgauth2args(config)

    LOG.info("pg_dumpall -g")
    for db in databases:
        LOG.info("pg_dump %s --format %s %s",
                 subprocess.list2cmdline(args),
                 config['pgdump']['format'],
                 db)
