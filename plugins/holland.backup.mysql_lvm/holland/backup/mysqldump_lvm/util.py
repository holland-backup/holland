"""Utility functions to help out the mysql-lvm plugin"""
import os
import shutil
import tempfile
import logging
from holland.core.exceptions import BackupError
from holland.lib.mysql import PassiveMySQLClient, MySQLError, \
                              build_mysql_config, connect
from holland.lib.compression import open_stream
from holland.lib.lvm import Snapshot
from holland.backup.mysqldump_lvm.actions import FlushAndLockMySQLAction, \
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
    name = config['snapshot-name'] or \
            logical_volume.lv_name + '_snapshot'
    extent_size = int(logical_volume.vg_extent_size)
    size = config['snapshot-size'] or \
            min(int(logical_volume.vg_free_count), # don't exceed vg_free_count
                (int(logical_volume.lv_size)*0.2) / extent_size,
                (15*1024**3) / extent_size # maximum 15G auto-sized snapshot space
               ) 
    mountpoint = config['snapshot-mountpoint']
    tempdir = False
    if not mountpoint:
        tempdir = True
        mountpoint = tempfile.mkdtemp()
    snapshot = Snapshot(name, size, mountpoint)
    if tempdir:
        snapshot.register('post-unmount', 
                          lambda *args, **kwargs: cleanup_tempdir(mountpoint))
    return snapshot

def setup_actions(snapshot, config, client):
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

def setup_mysqldump(snapshot, mysqldump_plugin, datadir):
    act = MySQLDumpDispatchAction(mysqldump_plugin, datadir)
    snapshot.register('post-mount', act, priority=100)
