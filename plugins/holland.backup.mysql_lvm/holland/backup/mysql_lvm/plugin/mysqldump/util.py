"""Utility functions to help out the mysql-lvm plugin"""
import os
import shutil
import tempfile
import logging
from holland.core import BackupError
from holland.core.util.fmt import format_bytes
from holland.lib.mysql import PassiveMySQLClient, MySQLError, \
                              build_mysql_config, connect
from holland.lib.lvm import Snapshot, parse_bytes
from holland.backup.mysql_lvm.actions import FlushAndLockMySQLAction, \
                                             RecordMySQLReplicationAction, \
                                             MySQLDumpDispatchAction
from holland.backup.mysql_lvm.plugin.common import log_final_snapshot_size
LOG = logging.getLogger(__name__)

def setup_actions(snapshot, config, client, datadir, spooldir, plugin):
    """Setup actions for a LVM snapshot based on the provided
    configuration.

    Optional actions:
        * MySQL locking
        * Recording MySQL replication
    """
    if config['mysql-lvm']['lock-tables']:
        extra_flush = config['mysql-lvm']['extra-flush-tables']
        act = FlushAndLockMySQLAction(client, extra_flush)
        snapshot.register('pre-snapshot', act, priority=100)
        snapshot.register('post-snapshot', act, priority=100)
    if config['mysql-lvm'].get('replication', True):
        repl_cfg = config.setdefault('mysql:replication', {})
        act = RecordMySQLReplicationAction(client, repl_cfg)
        snapshot.register('pre-snapshot', act, 0)

    mysqld_config = dict(config['mysqld'])
    mysqld_config['datadir'] = datadir
    if not mysqld_config['tmpdir']:
        mysqld_config['tmpdir'] = tempfile.gettempdir()

    ib_log_size = client.show_variable('innodb_log_file_size')
    if ib_log_size:
        mysqld_config['innodb-log-file-size'] = ib_log_size

    act = MySQLDumpDispatchAction(plugin, mysqld_config)
    snapshot.register('post-mount', act, priority=100)

    errlog_src = os.path.join(datadir, 'holland_lvm.log')
    errlog_dst = os.path.join(spooldir, 'holland_lvm.log')
    snapshot.register('pre-unmount',
                      lambda *args, **kwargs: shutil.copyfile(errlog_src,
                                                              errlog_dst)
                     )

    snapshot.register('pre-remove', log_final_snapshot_size)
