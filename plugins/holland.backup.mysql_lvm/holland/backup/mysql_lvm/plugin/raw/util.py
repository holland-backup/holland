"""Utility functions to help out the mysql-lvm plugin"""
import os
import shutil
import tempfile
import logging
from holland.lib.compression import open_stream
from holland.backup.mysql_lvm.actions import FlushAndLockMySQLAction, \
                                             RecordMySQLReplicationAction, \
                                             InnodbRecoveryAction, \
                                             TarArchiveAction
from holland.backup.mysql_lvm.plugin.common import log_final_snapshot_size

LOG = logging.getLogger(__name__)

def setup_actions(snapshot, config, client, snap_datadir, spooldir):
    """Setup actions for a LVM snapshot based on the provided
    configuration.

    Optional actions:
        * MySQL locking
        * InnoDB recovery
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
    if config['mysql-lvm']['innodb-recovery']:
        mysqld_config = dict(config['mysqld'])
        mysqld_config['datadir'] = snap_datadir
        if not mysqld_config['tmpdir']:
            mysqld_config['tmpdir'] = tempfile.gettempdir()
        act = InnodbRecoveryAction(mysqld_config)
        snapshot.register('post-mount', act, priority=100)
        errlog_src = os.path.join(snap_datadir, 'innodb_recovery.log')
        errlog_dst = os.path.join(spooldir, 'innodb_recovery.log')
        snapshot.register('pre-unmount',
                          lambda *args, **kwargs: shutil.copyfile(errlog_src, 
                                                                  errlog_dst)
                         )
    
        mycnf_src = os.path.join(snap_datadir, 'my.innodb_recovery.cnf')
        mycnf_dst = os.path.join(spooldir, 'my.innodb_recovery.cnf')
        snapshot.register('pre-unmount',
                          lambda *args, **kwargs: shutil.copyfile(mycnf_src, 
                                                                  mycnf_dst)
                         )


    archive_stream = open_stream(os.path.join(spooldir, 'backup.tar'),
                                 'w',
                                 **config['compression'])
    act = TarArchiveAction(snap_datadir, archive_stream, config['tar'])
    snapshot.register('post-mount', act, priority=50)

    snapshot.register('pre-remove', log_final_snapshot_size)
