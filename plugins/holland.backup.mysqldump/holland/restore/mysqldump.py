"""
Restore support for MySQLDump backups
"""

import os
import sys
import csv
import select
import codecs
import logging
from subprocess import *
from holland.core.command import Command, option
from holland.lib.compression import open_stream
from holland.backup.mysqldump import CONFIGSPEC
from mysqlrestore.mysqldump import Parser, SchemaFilter
from mysqlrestore.script import Progress
from mysqlrestore.rewrite import create_rewriter

class MySQLRestore(Command):
    """
    holland restore <backupset-name> dbname[=newdbname] [dbname[=newdbname]...]

    ${cmd_option_list}
    """
    name = 'mysql-restore'

    aliases = [
        'mr'
    ]

    options = [
        option('--force', action='store_true',
                help="Don't prompt for confirmation."),
        option('--output', '-o',
                help="Output to the specified file. If 'mysql' is specified, this will start a mysql process."),
        option('--all-databases', action='store_true',
                help="Restore all databases in this backupset"),
        option('--skip-binlog', dest='binlog', default=True, action='store_true',
                help='''Don't write this restore to the binary log.
                        This appends SQL_LOG_BIN=0 to the top of the restore file.'''),
        option('--progress', '-P', action='store_true', default=False,
                help='Show a progress bar')
    ]

    def __init__(self, backup=None):
        self.backup = backup
        Command.__init__(self)

    def run(self, cmd, opts, *databases):
        # 1) find the directory in the backupset
        # 2) if !file-per-database, use all-databases.sql
        # 3) otherwise, loop over data/MANIFEST.txt
        # 3a) apply database files before parsing file-per-database files
        #     to avoid doing too much work
        # 3b) Try to apply table exclusion filters if they have a '.'
        config = self.backup.config
        config.validate_config(CONFIGSPEC)
        if 'mysqldump' not in config:
            logging.info("Backupset %s is not a mysqldump backup.", self.backup.name)
            return 1

        if not opts.output:
            logging.error("No output destination was specified.  Specify '-' to output to the console.")
            return 1

        if not databases and not opts.all_databases:
            logging.info("No databases specified to restore.  Please specify some "
                  "database or use the --all-databases option to restore "
                  "everything from the backupset.")
            return 1

        databases = [db.decode('utf8') for db in databases]

        dbrewriter = create_rewriter(databases)

        if opts.all_databases:
            logging.info("Restoring all databases.")
            databases = None # restore all databases
        else:
            databases = dbrewriter.dbmap.keys() # only restore specified databases

        if opts.force:
            logging.warning("Skipping confirmation")
        else:
            logging.info("Confirmation should be done here.")

        schema_filter = SchemaFilter(databases=databases)

        if opts.output == 'mysql':
            pid = start_mysql()
            outfile = pid.stdin
        elif opts.output == '-':
            outfile = sys.stdout
        else:
            if os.path.exists(opts.output):
                logging.error("Refusing to overwrite %s", os.path.abspath(opts.output))
                return 1
            outfile = open(opts.output, 'w')

        if not config['mysqldump']['file-per-database']:
            path = os.path.join(self.backup.path, 'backup_data.sql')
            try:
                stream = open_stream(path, 'r', config['compression']['method'])
                stream = codecs.getreader('utf8')(stream)
            except IOError, exc:
                logging.error("Failed to open backup data stream: %s", exc)
                return 1
            handle_stream(stream, schema_filter, opts.binlog, opts.progress, dbrewriter=dbrewriter, outfile=outfile)
        else:
            manifest = os.path.join(self.backup.path, 'backup_data', 'MANIFEST.txt')
            for db, filename in csv.reader(open(manifest, 'r'),dialect=csv.excel_tab):
                if schema_filter.is_filtered(db, None):
                    logging.info("Skipping %s", db)
                    continue
                stream = open_stream(os.path.join(self.backup.path, 'backup_data', filename),
                                     'r', method=config['compression']['method'])
                logging.info("Restoring %s", db.decode('utf8'))
                handle_stream(stream, schema_filter, opts.binlog, opts.progress, dbrewriter=dbrewriter, outfile=outfile)
                stream.close()
                logging.info("Done with %s", stream.name)
        return 1

def start_mysql():
    return Popen(['mysql', '--default-character-set=utf8'], stdin=PIPE, close_fds=True)

def handle_stream(stream, filter, binlog, show_progress=False, dbrewriter=None, outfile=None):
    parser = Parser(stream, schema_filter=filter, binlog=binlog, dbrewriter=dbrewriter)

    if show_progress:
        progress = Progress(parser)
    else:
        progress = lambda x: 1 # noop

    for line in parser:
        while line:
            result = select.select([], [outfile.fileno()], [], 1.0)
            if result[1]: # <- wfds populated
                n = os.write(outfile.fileno(), line)
                line = line[n:]
            progress(n)
    progress(0)
