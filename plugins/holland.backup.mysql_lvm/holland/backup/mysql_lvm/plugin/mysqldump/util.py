"""Utility functions to help out the mysql-lvm plugin"""
import os
import shutil
import tempfile
import logging
from holland.core.exceptions import BackupError
from holland.core.util.fmt import format_bytes
from holland.lib.mysql import PassiveMySQLClient, MySQLError, \
                              build_mysql_config, connect
from holland.lib.compression import open_stream
from holland.lib.lvm import Snapshot, parse_bytes
from holland.backup.mysql_lvm.actions import FlushAndLockMySQLAction, \
                                             RecordMySQLReplicationAction, \
                                             MySQLDumpDispatchAction

LOG = logging.getLogger(__name__)

def connect_simple(config):
    """Create a MySQLClientConnection given a mysql:client config
    section from a holland mysql backupset
    """
    try:
        mysql_config = build_mysql_config(config)
        LOG.debug("mysql_config => %r", mysql_config)
        connection = connect(mysql_config['client'], PassiveMySQLClient)
        connection.connect()
        return connection
    except MySQLError, exc:
        raise BackupError("[%d] %s" % exc.args)

def cleanup_tempdir(path):
    LOG.info("Removing temporary mountpoint %s", path)
    shutil.rmtree(path)

def build_snapshot(config, logical_volume):
    """Create a snapshot process for running through the various steps
    of creating, mounting, unmounting and removing a snapshot
    """
    snapshot_name = config['snapshot-name'] or \
                    logical_volume.lv_name + '_snapshot'
    extent_size = int(logical_volume.vg_extent_size)
    snapshot_size = config['snapshot-size']
    if not snapshot_size:
        snapshot_size = min(int(logical_volume.vg_free_count),
                            (int(logical_volume.lv_size)*0.2) / extent_size,
                            (15*1024**3) / extent_size,
                           )
    else:
        try:
            snapshot_size = parse_bytes(snapshot_size) / extent_size
            if snapshot_size > int(logical_volume.vg_free_count):
                LOG.info("Snapshot size requested %s, but only %s available.",
                         config['snapshot-size'],
                         format_bytes(int(logical_volume.vg_free_count)*extent_size, precision=4))
                LOG.info("Truncating snapshot-size to %d extents (%s)",
                         int(logical_volume.vg_free_count),
                         format_bytes(int(logical_volume.vg_free_count)*extent_size, precision=4))
                snapshot_size = int(logical_volume.vg_free_count)
        except ValueError, exc:
            raise BackupError("Problem parsing snapshot-size %s" % exc)

    mountpoint = config['snapshot-mountpoint']
    tempdir = False
    if not mountpoint:
        tempdir = True
        mountpoint = tempfile.mkdtemp()
    snapshot = Snapshot(snapshot_name, int(snapshot_size), mountpoint)
    if tempdir:
        snapshot.register('post-unmount',
                          lambda *args, **kwargs: cleanup_tempdir(mountpoint))
    return snapshot

def setup_actions(snapshot, config, client, datadir, plugin):
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
    act = MySQLDumpDispatchAction(plugin, mysqld_config)
    snapshot.register('post-mount', act, priority=100)

    errlog_src = os.path.join(datadir, 'holland_lvm.log')
    errlog_dst = os.path.join(spooldir, 'holland_lvm.log')
    snapshot.register('pre-unmount',
                      lambda *args, **kwargs: shutil.copyfile(errlog_src,
                                                              errlog_dst)
                     )
