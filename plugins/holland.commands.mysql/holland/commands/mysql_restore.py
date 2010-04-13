import os
import sys
import glob
import time
import subprocess
import logging
import re
from tempfile import NamedTemporaryFile
from holland.core.command import Command, option
from holland.core.spool import spool
from holland.core.util.fmt import format_bytes, format_interval
from holland.core.util.template import Template
from holland.lib.compression import COMPRESSION_METHODS, open_stream
from holland.lib.which import which, WhichError
from inspect import getdoc
from plumbing import Plumber, ProgressMonitor

LOGGER = logging.getLogger(__name__)

class MySQLRestore(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Restores the specified backup.

    Example:

    # holland ${cmd_name} ${bk_set}
    """
    name = 'mysql-restore'
    aliases = [
        'mr'
    ]
    description = 'Restore a mysqldump backup and monitor the progress'

    def help(self):
        """
        Format this command's help output

        Default is to use the class' docstring as a 
        template and interpolate the name, options and 
        arguments
        """
        usage_str = getdoc(self) or ''
        usage_str = self.reformat_paragraphs(usage_str)
        cmd_name = self.name
        cmd_opts = self.format_cmd_options()
        cmd_args = self.format_cmd_args()
        bk_set = self.find_all_mysqldump_backups_str()[0]
        help_str = Template(usage_str).safe_substitute(cmd_name=cmd_name,
                                                   cmd_option_list=cmd_opts,
                                                   cmd_args=cmd_args,
                                                   cmd_usage=self.usage(),
                                                   bk_set=bk_set
                                                   ).rstrip()
        return re.sub(r'\n\n+', r'\n\n', help_str)


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

    def find_all_mysqldump_backups_str(self):
        plugin = 'holland:backup.plugin'
        backups = sum([b.list_backups() \
                       for b in spool.list_backupsets()],
                      [])

        return [b.name for b in backups \
                if b.config.lookup(plugin) == 'mysqldump']

    def run(self, cmd, opts, backup_name):
        # Try to find mysqldump-backup name in spool
        # if not, recommend checkin output of 'list-backups'
        # Check if holland:backup.plugin = mysqldump [if not, bork]
        # Locate backup_data.sql file - I guess glob("*.sql[.ext]") 
        # where ext is derived by the compression type (holland.lib.compression)

        # file-per-database = <db-name>.sql[.ext]
        # !file-per-database = backup_data.sql[.ext]
        backup = spool.find_backup(backup_name)

        if not backup or not backup.exists():
            print >>sys.stderr, "No such backup %s - Valid backups:" % \
                                (backup_name)

            for backup in self.find_all_mysqldump_backups_str():
                print >> sys.stderr, backup
            return 1

        config = backup.config

        plugin = config.lookup('holland:backup.plugin')

        if plugin != 'mysqldump':
            print >>sys.stderr, "This command only supports mysqldump backups"
        
        backups = self.find_all_backups(backup.path,config)

        try:
            mysql_bin = which('mysql')
        except WhichError, e:
            print >>sys.stderr, "Failed to find mysql client command: %s" % e
            return 1
        try:
            for sqlfile in backups:
                print "Restoring %r" % sqlfile
                filein = open_stream(sqlfile, 'r', config.lookup('compression.method'))
                # Try to get close to the real backup size
                ratio = config.lookup('holland:backup.on-disk-size') / config.lookup('holland:backup.estimated-size')
                total_size = os.stat(sqlfile).st_size / ratio
                stderr_file = NamedTemporaryFile()
                pid = subprocess.Popen([mysql_bin], stdin=subprocess.PIPE, stderr=stderr_file.fileno())
                ostream = pid.stdin
    
                start_time = time.time()
                plumber = Plumber(istream=filein, ostream=ostream, callback=ProgressMonitor(total_size))
                plumber.run()
                ostream.close()
                stderr_file.seek(0)
                err_msgs = stderr_file.read()
                stderr_file.close()
                print
                status = pid.wait()
                if err_msgs:
                    print "Error messages while spooling restore to mysql:"
                    print err_msgs
                now = time.time()
                print >>sys.stderr, "%s restored in %s [%s per second average]" % \
                        (sqlfile, format_interval(now - start_time),
                         format_bytes(plumber.output_bytes/ (now - start_time)))
                filein.close()
        except Exception, e:
            LOGGER.debug(e, exc_info=True)
            raise e
        except KeyboardInterrupt:
            print
            print >>sys.stderr, "Interrupt"
