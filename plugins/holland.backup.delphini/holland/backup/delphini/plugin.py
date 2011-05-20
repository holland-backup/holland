# coding: utf-8
"""
holland.backup.delphini.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implements a backup plugin for holland 1.0 which is exposed as
holland.backup entrypoint in the delphini package.

:copyright: 2010-2011 by Andrew Garner
:license: BSD, see LICENSE.rst for details
"""

import os
import glob
import logging
from holland.core import BackupPlugin, BackupError
from holland.backup.delphini.backend import backup
from holland.backup.delphini.util import run_command
from holland.backup.delphini.error import ClusterError

LOG = logging.getLogger(__name__)

class DelphiniPlugin(BackupPlugin):
    """MySQL Cluster Backup Plugin implementation for Holland"""

    def estimate(self):
        """Estimate the backup size"""
        # XXX: implement I_S querying or ssh du -sh perhaps
        return 0

    def backup(self):
        """Run a MySQL cluster backup"""
        config = self.config['mysql-cluster']
        dsn = config['connect-string']
        ssh_user = config['default-ssh-user']
        ssh_keyfile = config['default-ssh-keyfile']
        target_path = os.path.join(self.backup_directory, 'data')
        try:
            os.mkdir(target_path)
        except OSError, exc:
            raise BackupError("Failed to create %s: %s", (target_path, exc))

        try:
            backup_id, stop_gcp = backup(dsn,
                                         ssh_user,
                                         ssh_keyfile,
                                         target_path)
        except ClusterError, exc:
            raise BackupError(exc)

        cluster_info = os.path.join(self.backup_directory,
                                    'cluster_backup.info')
        try:
            fileobj = open(cluster_info, 'w')
        except IOError, exc:
            raise BackupError("Failed to create %s: %s", (cluster_info, exc))

        try:
            try:
                fileobj.write("stopgcp = %s\n" % stop_gcp)
                fileobj.write("backupid = %s\n" % backup_id)
            except IOError, exc:
                raise BackupError("Failed to write %s: %s",
                                  (cluster_info, exc))
        finally:
            fileobj.close()

        compression = self.config['compression']['method']

        if compression != 'none':
            path = os.path.join(self.backup_directory,
                                'BACKUP-%d' % backup_id,
                                '*')
            args = [
                compression,
                '-v',
                '-%d' % self.config['compression']['level'],
            ]
            if compression == 'lzop':
                # ensure lzop removes the old files once they're compressed
                args.insert(1, '--delete')
            for path in glob.glob(path):
                run_command(args + [path])

    def plugin_info(self):
        return dict(
            name='delphini',
            author='Holland Core Team',
            summary='MySQL Cluster backup plugin',
            description='''
            ''',
            version='1.0',
            api_version='1.1.0',
        )

    def configspec(self):
        """Provide the config specification for the delphini plugin"""
        return super(DelphiniPlugin, self).configspec().merge('''
        [mysql-cluster]
        connect-string      = string(default=localhost)
        default-ssh-user    = string(default=root)
        default-ssh-keyfile = string(default=None)

        [compression]
        method  = option(none, gzip, pigz, bzip2, lzma, lzop, default=gzip)
        level   = integer(min=1, max=9)
        ''')
