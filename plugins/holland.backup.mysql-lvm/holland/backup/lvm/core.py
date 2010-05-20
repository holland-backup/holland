"""Core functions for initializing LVM SnapshotLifecycles"""
import sys
from holland.backup.lvm.snapshot import SnapshotLifecycle
from holland.backup.lvm.util import mysqlhelper
from holland.backup.lvm.actions import TarBackup, \
                                       MySQLManager, \
                                       InnoDBRecovery

def mysql_snapshot_lifecycle(destination=sys.stdout,
                             snapshot_name=None,
                             snapshot_size=None,
                             snapshot_mountpoint=None,
                             mysql_auth=None,
                             flush_tables=True,
                             extra_flush_tables=True,
                             innodb_recovery=False,
                             replication_info_callback=None,
                             log_file=None):
    """Setup a Lvm state for a MySQL environment"""

    helper = mysqlhelper.connect(**mysql_auth)
    target_directory = helper.variable('datadir')
    lifecycle = SnapshotLifecycle(target_directory,
                                  snapshot_name=snapshot_name,
                                  snapshot_size=snapshot_size,
                                  snapshot_mountpoint=snapshot_mountpoint)
    archiver = TarBackup(dst=destination, tarlog=log_file)
    # backup() should be run after everything else
    lifecycle.add_callback('backup', archiver.backup, priority=99)

    # setup lock/unlock tables based on flush settings
    manager = MySQLManager(mysqlhelper=helper,
                           flush_tables=flush_tables,
                           extra_flush_tables=extra_flush_tables)
    lifecycle.add_callback('presnapshot', manager.lock, priority=50)
    if replication_info_callback:
        lifecycle.add_callback('presnapshot', 
                               lambda: replication_info_callback(helper),
                               priority=99)
    lifecycle.add_callback('postsnapshot', manager.unlock)

    # we could skip this, but instead we have the callback
    # log an explicit "We skipped innodb recovery"
    if innodb_recovery:
        ibrecovery = InnoDBRecovery()
        # ibrecovery should run before any other backup process,
        # so we lower the callback priority
        lifecycle.add_callback('backup', ibrecovery.run_recovery, priority=0)

    return lifecycle
