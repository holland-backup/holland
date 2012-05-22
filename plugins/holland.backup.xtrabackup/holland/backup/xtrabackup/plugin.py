"""holland backup plugin using xtrabackup"""

import os, sys
import shutil
import logging
import tempfile
from subprocess import list2cmdline, check_call, CalledProcessError, STDOUT
from holland.core.exceptions import BackupError
from holland.core.util.path import directory_size
from holland.lib.compression import open_stream
from holland.lib.mysql.option import build_mysql_config, write_options
from holland.lib.mysql.client import connect, MySQLError
from holland.backup.xtrabackup.util import xtrabackup_version, \
                                           get_stream_method, \
                                           resolve_template, \
                                           run_pre_command

LOG = logging.getLogger(__name__)

CONFIGSPEC = """
[xtrabackup]
global-defaults = string(default='/etc/my.cnf')
innobackupex    = string(default='innobackupex-1.5.1')
ibbackup        = string(default=None)
stream          = option(yes,no,tar,xbstream,default=tar)
slave-info      = boolean(default=no)
safe-slave-backup = boolean(default=no)
no-lock         = boolean(default=no)
tmpdir          = string(default=None)
additional-options = force_list(default=list())
pre-command     = string(default=None)

[compression]
method          = option('none', 'gzip', 'pigz', 'bzip2', 'lzma', 'lzop', default='gzip')
inline          = boolean(default=yes)
level           = integer(min=0, max=9, default=1)

[mysql:client]
defaults-extra-file = force_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(min=0, default=None)
""".splitlines()

class XtrabackupPlugin(object):
    """This plugin provides support for backing up a MySQL database using
    xtrabackup from Percona
    """

    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.config.validate_config(CONFIGSPEC)
        self.target_directory = target_directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        """Estimate the size of the backup this plugin will produce"""
        try:
            mysql_config = build_mysql_config(self.config['mysql:client'])
            client = connect(mysql_config['client'])
            datadir = client.show_variable('datadir')
            return directory_size(datadir)
        except MySQLError, exc:
            raise BackupError("Failed to lookup the MySQL datadir when "
                              "estimating backup size: [%d] %s" % exc.args)

    def backup(self):
        """Run a database backup with xtrabackup"""
        defaults_file = os.path.join(self.target_directory, 'my.xtrabackup.cnf')
        args = [
            self.config['xtrabackup']['innobackupex'],
            '--defaults-file=%s' % defaults_file,
        ]

        if self.config['xtrabackup']['ibbackup']:
            args.append('--ibbackup=' + self.config['xtrabackup']['ibbackup'])

        backup_directory = self.target_directory
        stream_method = get_stream_method(self.config['xtrabackup']['stream'])
        if stream_method:
            args.append('--stream=' + stream_method)
        else:
            backup_directory = os.path.join(backup_directory, 'data')
            args.append('--no-timestamp')
        if self.config['xtrabackup']['tmpdir']:
            args.append('--tmpdir=' + self.config['xtrabackup']['tmpdir'])
        if self.config['xtrabackup']['slave-info']:
            args.append('--slave-info')
        if self.config['xtrabackup']['safe-slave-backup']:
            args.append('--safe-slave-backup')
        if self.config['xtrabackup']['no-lock']:
            args.append('--no-lock')
        if self.config['xtrabackup']['additional-options']:
            args.extend(self.config['xtrabackup']['additional-options'])
        args.append(backup_directory)


        if self.config['xtrabackup']['pre-command']:
            cmd = resolve_template(self.config['xtrabackup']['pre-command'],
                                   backupdir=self.target_directory)
            if self.dry_run:
                LOG.info("Skipping pre-command in dry-run mode: %s", cmd)
            else:
                run_pre_command(cmd)

        LOG.info("%s", list2cmdline(args))
        if self.dry_run:
            return


        config = build_mysql_config(self.config['mysql:client'])
        write_options(config, defaults_file)
        shutil.copyfileobj(open(self.config['xtrabackup']['global-defaults'], 'r'),
                           open(defaults_file, 'a'))

        if stream_method:
            stdout_path = os.path.join(self.target_directory, 'backup.tar')
            stdout = open_stream(stdout_path, 'w',
                                 **self.config['compression'])
            stderr_path = os.path.join(self.target_directory, 'xtrabackup.log')
            stderr = open(stderr_path, 'wb')
        else:
            stdout_path = os.path.join(self.target_directory, 'xtrabackup.log')
            stderr_path = stdout_path
            stdout = open(stdout_path, 'wb')
            stderr = STDOUT

        try:
            try:
                check_call(args,
                           stdout=stdout,
                           stderr=stderr,
                           close_fds=True)
            except OSError, exc:
                LOG.info("Command not found: %s", args[0])
                raise BackupError("%s not found. Is xtrabackup installed?" %
                                  args[0])
            except CalledProcessError, exc:
                LOG.info("%s failed", list2cmdline(exc.cmd))
                for line in open(stderr_path, 'rb'):
                    if line.startswith('>>'):
                        continue
                    LOG.error("%s", line.rstrip())
                raise BackupError("%s failed" % exc.cmd[0])
        finally:
            exc_info = sys.exc_info()[1]
            try:
                stdout.close()
                if stderr != STDOUT:
                    stderr.close()
            except IOError, exc:
                if not exc_info:
                    raise BackupError(str(exc))

    def info(self):
        """Provide information about the backup this plugin produced"""
        return ""
