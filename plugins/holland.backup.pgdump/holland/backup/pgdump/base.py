# -*- coding: utf-8 -*-
"""Backup functions for pg_dump"""

# Python stdlib
import os
import tempfile
import logging
import subprocess

# 3rd party Postgres db connector
import psycopg2 as dbapi
# Holland general compression functions
from holland.lib.compression import open_stream

LOG = logging.getLogger(__name__)

class PgError(Exception):
    """Raised when any error associated with Postgres occurs"""

def get_connection(config):
    args = {}
    # remap pgauth parameters to what psycopg2.connect accepts
    remap = { 'hostname' : 'host', 'username' : 'user' }
    for key in ('hostname', 'port', 'username', 'password'):
        value = config['pgauth'].get(key)
        key = remap.get(key, key)
        if value is not None:
            args[key] = value
    connection = dbapi.connect(database='template1', **args)

    if config["pgauth"]["role"]:
        cursor = connection.cursor()
        cursor.execute("SET ROLE %s" % config["pgauth"]["role"])
    return connection
    
def get_db_size(dbname, connection):
    cursor = connection.cursor()
    cursor.execute("SELECT pg_database_size('%s')" % dbname)
    size = int(cursor.fetchone()[0])
    LOG.info("DB %s size %d" % (dbname, size))
    return size

def pg_databases(config, connection):
    """Find the databases available in the Postgres cluster specified
    in config['pgpass']
    """
    # FIXME: use PGPASSFILE
    cursor = connection.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate='f'")
    databases = [db for db, in cursor]
    cursor.close()
    #connection.close()
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
    # FIXME: use PGPASSFILE
    args = [ 'pg_dump' ] + connection_params + [
        '--format', format,
        dbname
    ]

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

    stderr = tempfile.TemporaryFile()
    returncode = subprocess.call(['pg_dumpall', '-g'] + connection_params,
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
        raise PgError("pg_dumpall exited with non-zero status[%d]" %
                      returncode)

def pgauth2args(config):
    args = []
    remap = { 'hostname' : 'host' }
    for param in ('hostname', 'port', 'username', 'role'):
        value = config.get(param)
        key = remap.get(param, param)
        if value is not None:
            args.extend(['--%s' % key, str(value)])
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
    connection_params = pgauth2args(config['pgauth'])
 
    pgpass_file = generate_pgpassfile(backup_directory,
                                      config['pgauth']['password'])
    pgenv = dict(os.environ)
    pgenv['PGPASSFILE'] = pgpass_file

    backup_globals(backup_directory, config, connection_params, env=pgenv)

    for dbname in databases:
        # FIXME: potential problems with weird dataase names
        #        Consider: 'foo/bar' or unicode names
        # FIXME: compression usually doesn't make sense with --format=custom
        
        filename = os.path.join(backup_directory, dbname + '.dump')
        
        stream = open_stream(filename, 'w', **config['compression'])
        run_pgdump(dbname=dbname, 
                   output_stream=stream, 
                   connection_params=connection_params + extra_args,
                   format=config['pgdump']['format'], 
                   env=pgenv)
        stream.close()
