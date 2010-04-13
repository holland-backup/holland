import os
import sys
import time
import glob
import subprocess
from holland.core.command import Command, option
from holland.core.spool import spool
from holland.lib.compression import COMPRESSION_METHODS, open_stream
from mysqldump_parser import MySQLDumpParser

def log_it(event_name, item, lineno, offset_start, offset_end):
    #print "event=%s item=%s lineno=%d offset=%d" % (event_name, item, lineno, offset)
    if event_name == 'database':
        print "Database: %s [line=%d byte-offset=%d..%d]" % (item, lineno, offset_start, offset_end)
    elif event_name == 'table_schema':
        print "\tTable: %s " % (item)
        print "\t\tDDL [line=%d byte_offset=%d..%d]" % (lineno, offset_start, offset_end)
    elif event_name == 'table_data':
        print "\t\tData [line=%d byte-offset=%d..%d]" % (lineno, offset_start, offset_end)
    elif event_name == 'fake_view':
        print "\tInitial View (temp table): %s [line=%d byte-offset=%d..%d]" % (item, lineno, offset_start, offset_end)
    elif event_name == 'final_view':
        print "\tFinal View: %s [line=%d byte-offset=%d..%d]" % (item, lineno, offset_start, offset_end)

class MySQLIndexList(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Generates a table-of-contents for a mysqldump backup.
    This lists the databases, tables, views, routines and 
    shows the line # and byte-offsets to extract each 
    schema object.

    Example:

    # holland ${cmd_name} default/20090514_120000

    /var/spool/holland/default/20090514_120000/backup_data.sql.gz

    =============================================================

    Database: mysql [line=16 byte-offset=386]

        Table: columns_priv 

                DDL [line=17 byte_offset=415]

                Data [line=18 byte-offset=459]
    ....
    """
    name = 'mysql-list'
    aliases = [
        'ml'
    ]
    description = 'List the table-of-contents of a mysqldump sql files.'

    def find_all_backups(self, path, config):
        if config.lookup('compression.level') > 1:
            method = config.lookup('compression.method')
            ext = COMPRESSION_METHODS[method][1]
        else:
            ext = ''

        if config['mysqldump'].as_bool('file-per-database'):
            return glob.glob(os.path.join(path, 'backup_data', '*.sql' + ext))
        else:
            return glob.glob(os.path.join(path, 'backup_data.sql' + ext))

    def run(self, cmd, opts, mysqldump_backup):
        # Try to find mysqldump-backup name in spool
        # if not, recommend checkin output of 'list-backups'
        # Check if holland:backup.plugin = mysqldump [if not, bork]
        # Locate backup_data.sql file - I guess glob("*.sql[.ext]") 
        # where ext is derived by the compression type (holland.lib.compression)

        # file-per-database = <db-name>.sql[.ext]
        # !file-per-database = backup_data.sql[.ext]
        backup = spool.find_backup(mysqldump_backup)

        if not backup or not backup.exists():
            print >>sys.stderr, "No such backup %s - try holland list-backups" % (mysqldump_backup)
            return 1

        config = backup.config

        plugin = config.lookup('holland:backup.plugin')

        if plugin != 'mysqldump':
            print >>sys.stderr, "This command works only with mysqldump based backups, but %s used the %s plugin" % (backup.name, plugin)
        
        backups = self.find_all_backups(backup.path,config)
        
        for sqlfile in backups:
            time_initial = time.time()
            fileobj = open_stream(sqlfile, 'r', config.lookup('compression.method'))
            offset = 0
            print sqlfile
            print "=" * len(sqlfile)
            parser = MySQLDumpParser(fileobj, log_it)
            parser.parse()
            fileobj.close()
