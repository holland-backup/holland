import os
import sys
import time
import re
import glob
import fnmatch
import subprocess
from holland.core.command import Command, option
from holland.core.spool import spool
from holland.lib.compression import COMPRESSION_METHODS, open_stream

__all__ = [
    'MySQLExtractTable'
]

def stream_header(stream):
    # extra header
    from StringIO import StringIO
    eoh = False
    header_str = StringIO()
    for ln in stream:
        print >>header_str, ln,
        if ln == '\n':
            if not eoh:
                eoh = True
            else:
                break
    return header_str.getvalue()

def stream_sql(stream, glob_list=None, header=''):
    current_db = None
    header_output = False

    for n, ln in enumerate(stream):
        if ln.startswith('-- '):
            if ln.startswith('-- Current Database: '):
                current_db = ln.split()[-1][1:-1]
            obj = ln.split()[-1][1:-1]
            if current_db:
                qname = '%s.%s' % (current_db, obj)
            else:
                qname = ''
            matched = False
            for x in (glob_list or []):
                if x.match(qname) or x.match(obj):
                    matched = True
                    break
            if not matched:
                continue
            if not header_output:
                print header
            print "--"
            print ln,
            eoh = False
            for ln in stream:
                print ln,
                if ln == "--":
                        break


class MySQLExtractTable(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Extract items from a mysqldump sql file based on supplied patterns.

    Example:

    # Extract the mysql database

    # holland ${cmd_name} -g "mysql.*" default/20090514_120000
    """

    name = 'mysql-extract'

    aliases = [
        'mx'
    ]

    options = [
        option('-g', '--glob', action='append', default=[],
                help="Match tables according to a given glob.  May be specified multiple times."),
        option('-r', '--regex', action='append',default=[],
                help="Match tables according to the given regular expression.  May be specified multiple times.")
    ]

    description = 'Extract selective items from a mysqldump sql file.'

    def find_all_backups(self, path, config):
        if config.lookup('compression.level') >= 1:
            method = config.lookup('compression.method')
            ext = COMPRESSION_METHODS[method][1]
        else:
            ext = ''

        if config.lookup('mysqldump.file-per-database'):
            return glob.glob(os.path.join(path, 'backup_data', '*.sql' + ext))
        else:
            return glob.glob(os.path.join(path, 'backup_data.sql' + ext))

    def run(self, cmd, opts, backup):
        # Try to find mysqldump-backup name in spool
        # if not, recommend checkin output of 'list-backups'
        # Check if holland:backup.plugin = mysqldump [if not, bork]
        # Locate backup_data.sql file - I guess glob("*.sql[.ext]") 
        # where ext is derived by the compression type (holland.lib.compression)

        regex = list(opts.regex)
        regex.extend(map(fnmatch.translate, opts.glob))
        regex = map(re.compile, regex)

        # file-per-database = <db-name>.sql[.ext]
        # !file-per-database = backup_data.sql[.ext]
        backup = spool.find_backup(backup)

        if not backup or not backup.exists():
            print >>sys.stderr, "No such backup %s - try holland list-backups" % (backup)
            return 1

        config = backup.config

        plugin = config.lookup('holland:backup.plugin')

        if plugin != 'mysqldump':
            print >>sys.stderr, "Fail"
        else:
            print >>sys.stderr, "Okay - mysqldump based backup"
        
        backups = self.find_all_backups(backup.path,config)

        print >>sys.stderr, "Found backup files: %r" % backups

        for sqlfile in backups:
            time_initial = time.time()
            
            stream = open_stream(sqlfile, 'r', config.lookup('compression.method'))
            header_str = stream_header(stream)
            stream_sql(stream, regex, header_str)
            stream.close()
        return 0
