"""Utility functions to help out the mysql-lvm plugin"""
import os
import shutil
import tempfile
import logging
from holland.core.backup import BackupError
from holland.core.util.fmt import format_bytes
from holland.lib.mysql import PassiveMySQLClient, MySQLError, \
                              build_mysql_config, connect
from holland.lib.lvm import Snapshot, parse_bytes
from holland.backup.mysql_lvm.actions import FlushAndLockMySQLAction, \
                                             RecordMySQLReplicationAction, \
                                             MySQLDumpDispatchAction
from holland.backup.mysql_lvm.plugin.common import log_final_snapshot_size, \
                                                   connect_simple
from holland.backup.mysql_lvm.plugin.innodb import MySQLPathInfo, check_innodb

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

    if client.show_variable('have_innodb') == 'YES':
        pathinfo = MySQLPathInfo.from_mysql(client)
        check_innodb(pathinfo)

        ib_log_size = client.show_variable('innodb_log_file_size')
        if ib_log_size:
            mysqld_config['innodb-log-file-size'] = ib_log_size

        ibd_home_dir = pathinfo.innodb_data_home_dir
        if ibd_home_dir:
            # innodb_data_home_dir is set to something
            ibd_home_dir = pathinfo.remap_path(pathinfo.get_innodb_datadir(),
                                               snapshot.mountpoint)
            mysqld_config['innodb-data-home-dir'] = ibd_home_dir
            LOG.info("Remapped innodb-data-home-dir from %s to %s for snapshot",
                     pathinfo.get_innodb_datadir(), ibd_home_dir)

        ibd_file_path = pathinfo.innodb_data_file_path
        if ibd_file_path:
            ibd_file_path = pathinfo.remap_tablespaces(snapshot.mountpoint)
            mysqld_config['innodb-data-file-path'] = ibd_file_path
            if ibd_file_path != pathinfo.innodb_data_file_path:
                LOG.info("Remapped innodb-data-file-path from %s to %s for snapshot",
                         pathinfo.innodb_data_file_path, ibd_file_path)
                if not ibd_home_dir:
                    LOG.info("Remapped one or more tablespaces but "
                             "innodb-data-home-dir is not set. Setting "
                             "innodb-data-home-dir = '' to support absolute "
                             "tablespace paths on snapshot.")
                    mysqld_config['innodb-data-home-dir'] = ""

        ib_logdir = pathinfo.innodb_log_group_home_dir
        if ib_logdir and ib_logdir != './':
            ib_logdir = pathinfo.remap_path(pathinfo.get_innodb_logdir(),
                                            snapshot.mountpoint)
            mysqld_config['innodb-log-group-home-dir'] = ib_logdir
            LOG.info("Remapped innodb-log-group-home-dir from %s to %s for snapshot",
                     pathinfo.get_innodb_logdir(), ib_logdir)

    act = MySQLDumpDispatchAction(plugin, mysqld_config)
    snapshot.register('post-mount', act, priority=100)

    log_file = mysqld_config['log-error']
    if os.path.isfile(os.path.join(datadir, log_file)):
        errlog_src = os.path.join(datadir, log_file)
    else:
        errlog_src = log_file
    errlog_dst = os.path.join(spooldir, 'holland_lvm.log')
    snapshot.register('pre-unmount',
                      lambda *args, **kwargs: shutil.copyfile(errlog_src,
                                                              errlog_dst)
                     )

    snapshot.register('pre-remove', log_final_snapshot_size)
