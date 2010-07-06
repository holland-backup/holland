"""MySQL LVM snapshot backups"""

import os
import tempfile
import logging
from holland.lib.lvm import LogicalVolume, CallbackFailuresError, \
                            LVMCommandError, relpath, getmount
from holland.lib.mysql.client import MySQLError
from holland.core.util.path import directory_size
from holland.core.exceptions import BackupError
from holland.backup.mysql_lvm.plugin.mysqldump.util import connect_simple, \
                                                           build_snapshot, \
                                                           setup_actions
from holland.backup.mysqldump import MySQLDumpPlugin

LOG = logging.getLogger(__name__)

CONFIGSPEC = """
[mysql-lvm]
# default: mysql lv + _snapshot
snapshot-name = string(default=None)

# default: minimum of 20% of mysql lv or mysql vg free size
snapshot-size = string(default=None)

# default: temporary directory
snapshot-mountpoint = string(default=None)

# default: flush tables with read lock by default
lock-tables = boolean(default=yes)

# default: do an extra (non-locking) flush tables before
#          run flush tables with read lock
extra-flush-tables = boolean(default=yes)

[mysqld]
mysqld-exe              = force_list(default=list('mysqld', '/usr/libexec/mysqld'))
user                    = string(default='mysql')
innodb-buffer-pool-size = string(default=128M)
key-buffer-size         = string(default=16M)
tmpdir                  = string(default=None)

""".splitlines() + MySQLDumpPlugin.CONFIGSPEC

class MysqlDumpLVMBackup(object):
    """A Holland Backup plugin suitable for performing LVM snapshots of a 
    filesystem underlying a live MySQL instance.

    This plugin produces tar archives of a MySQL data directory.
    """
    CONFIGSPEC = CONFIGSPEC

    def __init__(self, name, config, target_directory, dry_run=False):
        self.config = config
        self.config.validate_config(self.CONFIGSPEC)
        LOG.debug("Validated config: %r", self.config)
        self.name = name
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.client = connect_simple(self.config['mysql:client'])
        self.mysqldump_plugin = MySQLDumpPlugin(name, config, target_directory, dry_run)

    def estimate_backup_size(self):
        """Estimate the backup size this plugin will produce

        This is currently the total directory size of the MySQL datadir
        """

        return self.mysqldump_plugin.estimate_backup_size()

    def configspec(self):
        """INI Spec for the configuration values this plugin supports"""
        return self.CONFIGSPEC
    
    def backup(self):
        """Run a backup by running through a LVM snapshot against the device
        the MySQL datadir resides on
        """
        # connect to mysql and lookup what we're supposed to snapshot
        self.client.connect()
        datadir = os.path.realpath(self.client.show_variable('datadir'))
        LOG.info("Backing up %s via snapshot", datadir)
        # lookup the logical volume mysql's datadir sits on
        try:
             volume = LogicalVolume.lookup_from_fspath(datadir)
        except LookupError, exc:
            raise BackupError("Failed to lookup logical volume for %s: %s" %
                              (datadir, str(exc)))

        if self.dry_run:
            _dry_run(volume)
            # do the normal mysqldump dry-run
            return self.mysqldump_plugin.backup()

        # create a snapshot manager
        snapshot = build_snapshot(self.config['mysql-lvm'], volume)
        # calculate where the datadirectory on the snapshot will be located
        rpath = relpath(datadir, getmount(datadir))
        snap_datadir = os.path.abspath(os.path.join(snapshot.mountpoint, rpath))
        # setup actions to perform at each step of the snapshot process
        setup_actions(snapshot=snapshot,
                      config=self.config,
                      client=self.client,
                      datadir=snap_datadir,
                      spooldir=self.target_directory,
                      plugin=self.mysqldump_plugin)

        try:
            snapshot.start(volume)
        except CallbackFailuresError, exc:
            # XXX: one of our actions failed.  Log this better
            for callback, error in exc.errors:
                LOG.error("%s", error)
            raise BackupError("Error occurred during snapshot process. Aborting.")
        except LVMCommandError, exc:
            # Something failed in the snapshot process
            raise BackupError(str(exc))

def _dry_run(volume):
    """Implement dry-run for LVM snapshots.  Not much to do here at the moment
    """
    LOG.info("[dry-run] Snapshotting %s/%s to %s/%s_snapshot",
             volume.vg_name,
             volume.lv_name,
             volume.vg_name,
             volume.lv_name)
