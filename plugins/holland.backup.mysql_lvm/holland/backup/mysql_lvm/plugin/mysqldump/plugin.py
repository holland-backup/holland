"""MySQL LVM snapshot backups"""

import os
import tempfile
import logging
from holland.core import BackupPlugin, BackupError, Configspec, load_plugin
from holland.core.util import directory_size
from holland.lib.lvm import LogicalVolume, CallbackFailuresError, \
                            LVMCommandError, relpath, getmount
from holland.lib.mysql.client import MySQLError
from holland.backup.mysql_lvm.plugin.common import build_snapshot, \
                                                   connect_simple
from holland.backup.mysql_lvm.plugin.mysqldump.util import setup_actions

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

""".splitlines()

class MysqlDumpLVMBackup(BackupPlugin):
    """A Holland Backup plugin suitable for performing LVM snapshots of a
    filesystem underlying a live MySQL instance.

    This plugin runs mysqldump against an instance of mysqld whose datadir
    is located on an LVM snapshot volume.
    """
    CONFIGSPEC = CONFIGSPEC

    def __init__(self, name):
        self.name = name
        self.client = None
        self.mysqldump_plugin = None

    def pre(self):
        self.client = connect_simple(self.config['mysql:client'])
        self.mysqldump_plugin = load_plugin('holland.backup', 'mysqldump')
        self.mysqldump_plugin.configure(self.config)
        self.mysqldump_plugin.setup(self.store)

    def estimate(self):
        """Estimate the backup size this plugin will produce

        This returns the estimate from the mysqldump plugin
        """
        return self.mysqldump_plugin.estimate_backup_size()

    def configspec(self):
        """INI Spec for the configuration values this plugin supports"""
        spec = load_plugin('holland.backup', 'mysqldump').configspec()
        spec.merge(Configspec.parse(self.CONFIGSPEC))
        return spec

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
                      spooldir=self.store.path,
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
            raise BackupError(exc)

    def plugin_info(self):
        return dict(
            name='mysqldump-lvm',
            summary='mysqldump backups off an LVM snapshot',
            author='Rackspace',
            version='1.1',
            api_version='1.1.0',
        )
