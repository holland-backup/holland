"""holland backup plugin using xtrabackup"""

import os
import shutil
import logging
import tempfile
from subprocess import list2cmdline, check_call, CalledProcessError
from holland.core import BackupError, BackupPlugin, open_stream
from holland.core.util.path import directory_size
from holland.lib.mysql.option import build_mysql_config, write_options
from holland.lib.mysql.client import connect, MySQLError

LOG = logging.getLogger(__name__)

CONFIGSPEC = """
[xtrabackup]
global-defaults = string(default='/etc/my.cnf')
innobackupex    = string(default='innobackupex-1.5.1')
stream          = boolean(default=yes)
slave-info      = boolean(default=no)
no-lock         = boolean(default=no)

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
"""

class XtrabackupPlugin(BackupPlugin):
    """This plugin provides support for backing up a MySQL database using
    xtrabackup from Percona
    """
    dry_run = False

    def estimate(self):
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
        defaults_file = os.path.join(self.backup_directory, 'my.xtrabackup.cnf')
        args = [
            self.config['xtrabackup']['innobackupex'],
            '--defaults-file=%s' % defaults_file,
            '--stream=tar4ibd',
            tempfile.gettempdir(),
        ]

        if self.config['xtrabackup']['slave-info']:
            args.insert(3, '--slave-info')
        if self.config['xtrabackup']['no-lock']:
            args.insert(2, '--no-lock')

        LOG.info("%s", list2cmdline(args))

        if self.dry_run:
            return

        config = build_mysql_config(self.config['mysql:client'])
        write_options(config, defaults_file)
        shutil.copyfileobj(open(self.config['xtrabackup']['global-defaults']),
                           open(defaults_file, 'a'))

        backup_path = os.path.join(self.backup_directory, 'backup.tar')
        compression_stream = open_stream(backup_path, 'w',
                                         **self.config['compression'])
        error_log_path = os.path.join(self.backup_directory, 'xtrabackup.log')
        error_log = open(error_log_path, 'wb')
        try:
            try:
                check_call(args,
                           stdout=compression_stream,
                           stderr=error_log,
                           close_fds=True)
            except CalledProcessError, exc:
                LOG.info("%s failed", list2cmdline(exc.cmd))
                for line in open(error_log_path, 'r'):
                    if line.startswith('>>'):
                        continue
                    LOG.info("%s", line.rstrip())
                raise BackupError("%s failed" % exc.cmd[0])
        finally:
            error_log.close()
            compression_stream.close()

    def dryrun(self):
        self.dry_run = True
        self.backup()

    def plugin_info(self):
        """Provide information about the backup this plugin produced"""
        return dict(
            name='xtrabackup',
            summary='xtrabackup innodb hot backup plugin for holland',
            description='',
            version='1.1',
            api_version='1.1.0',
        )
