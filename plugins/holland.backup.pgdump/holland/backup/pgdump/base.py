# -*- coding: utf-8 -*-
"""Backup functions for pg_dump"""

# Python stdlib
import os
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
    pgpass = config['pgauth']['pgpass']
    with open(pgpass, "r") as f:
        passline = f.readline()
    hostname, port, database, username, password = passline.split(':', 4)
    
    global connection
    connection = dbapi.connect(host=hostname, port=port, database=database, user=username, password=password)
    
def get_db_size(dbname):
    cursor = connection.cursor()
    cursor.execute("SELECT pg_database_size('%s')" % dbname)
    size = int(cursor.fetchone()[0])
    LOG.info("DB %s size %d" % (dbname, size))
    return size

def pg_databases(config):
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

def run_pgdump(dbname, output_stream):
    """Run pg_dump for the given database and write to the specified output
    stream.

    :param db: database name
    :type db: str
    :param output_stream: a file-like object - must have a fileno attribute
                          that is a real, open file descriptor
    """
    # FIXME: use PGPASSFILE
    args = [
        'pg_dump',
        '-Fc',
        dbname
    ]

    returncode = subprocess.call(args,
                                 stdout=output_stream,
                                 stderr=open('pgdump.err', 'a'),
                                 close_fds=True)
    # FIXME: write error output to LOG.error()
    if returncode != 0:
        raise OSError("%s failed.  Please check pgdump.err log" %
                      subprocess.list2cmdline(args))

def backup_globals(backup_directory, config):
    """Backup global Postgres data that wouldn't otherwise
    be captured by pg_dump.

    Runs pg_dumpall -g > $backup_dir/globals.sql

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
    :raises: OSError, PgError on error
    """

    path = os.path.join(backup_directory, 'global.sql')
    output_stream = open_stream(path, 'w', **config['compression'])

    # FIXME: use PGPASSFILE
    returncode = subprocess.call(['pg_dumpall', '-g'],
                                 stdout=output_stream,
                                 stderr=open('pgdump.err', 'a'),
                                 close_fds=True)
    output_stream.close()
    if returncode != 0:
        raise PgError("pg_dumpall exited with non-zero status[%d]" %
                      returncode)

def backup_pgsql(backup_directory, config, databases):
    """Backup databases in a Postgres instance

    :param backup_directory: directory to save pg_dump output to
    :param config: PgDumpPlugin config dictionary
    :raises: OSError, PgError on error
    """
    backup_globals(backup_directory, config)

    for dbname in databases:
        # FIXME: potential problems with weird dataase names
        #        Consider: 'foo/bar' or unicode names
        # FIXME: compression usually doesn't make sense with --format=custom
        
        filename = os.path.join(backup_directory, dbname + '.dump')
        
        stream = open_stream(filename, 'w', **config['compression'])
        run_pgdump(dbname, stream)
        stream.close()
