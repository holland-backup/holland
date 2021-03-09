"""MySQL LVM snapshot backups"""

import logging
import os

from holland.backup.mysql_lvm.plugin.common import (
    _dry_run,
    build_snapshot,
    connect_simple,
)
from holland.backup.mysql_lvm.plugin.raw.util import setup_actions
from holland.core.backup import BackupError
from holland.core.util.path import directory_size
from holland.lib.compression import COMPRESSION_CONFIG_STRING
from holland.lib.lvm import (
    CallbackFailuresError,
    LogicalVolume,
    LVMCommandError,
    getmount,
    relpath,
)
from holland.lib.mysql.client import MySQLError
from holland.lib.mysql.client.base import MYSQL_CLIENT_CONFIG_STRING

LOG = logging.getLogger(__name__)

CONFIGSPEC = (
    """
[mysql-lvm]
# default: mysql lv + _snapshot
snapshot-name = string(default=None)

# default: minimum of 20% of mysql lv or mysql vg free size
snapshot-size = string(default=None)

# default: temporary directory
snapshot-mountpoint = string(default=None)

# default: no
innodb-recovery = boolean(default=no)

# ignore errors due to strange innodb configurations
force-innodb-backup = boolean(default=no)

# default: flush tables with read lock by default
lock-tables = boolean(default=yes)

# default: do an extra (non-locking) flush tables before
#          run flush tables with read lock
extra-flush-tables = boolean(default=yes)

# default: create tar file from snapshot
archive-method      = option(dir,tar,default="tar")

[mysqld]
mysqld-exe              = force_list(default=list('mysqld', '/usr/libexec/mysqld'))
user                    = string(default='mysql')
innodb-buffer-pool-size = string(default=128M)
tmpdir                  = string(default=None)

[tar]
exclude = force_list(default='mysql.sock')
post-args = string(default=None)
pre-args = string(default=None)
"""
    + MYSQL_CLIENT_CONFIG_STRING
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


class MysqlLVMBackup(object):
    """
    A Holland Backup plugin suitable for performing LVM snapshots of a
    filesystem underlying a live MySQL instance.

    This plugin produces tar archives of a MySQL data directory.
    """

    CONFIGSPEC = CONFIGSPEC

    def __init__(self, name, config, target_directory, dry_run=False):
        self.config = config
        self.config.validate_config(self.configspec())
        LOG.debug("Validated config: %r", self.config)
        self.name = name
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.client = connect_simple(self.config["mysql:client"])

    def estimate_backup_size(self):
        """Estimate the backup size this plugin will produce

        This is currently the total directory size of the MySQL datadir
        """
        try:
            self.client.connect()
            datadir = self.client.show_variable("datadir")
            self.client.disconnect()
        except MySQLError as exc:
            raise BackupError("[%d] %s" % exc.args)
        return directory_size(datadir)

    def configspec(self):
        """INI Spec for the configuration values this plugin supports"""
        return self.CONFIGSPEC

    def backup(self):
        """Run a backup by running through a LVM snapshot against the device
        the MySQL datadir resides on
        """
        # connect to mysql and lookup what we're supposed to snapshot
        try:
            self.client.connect()
            datadir = os.path.realpath(self.client.show_variable("datadir"))
        except MySQLError as exc:
            raise BackupError("[%d] %s" % exc.args)

        LOG.info("Backing up %s via snapshot", datadir)
        # lookup the logical volume mysql's datadir sits on

        try:
            volume = LogicalVolume.lookup_from_fspath(datadir)
        except LookupError as exc:
            raise BackupError("Failed to lookup logical volume for %s: %s" % (datadir, str(exc)))
        except Exception as ex:
            raise BackupError("Failed to lookup logical volume for %s: %s" % (datadir, str(ex)))

        # create a snapshot manager
        snapshot = build_snapshot(self.config["mysql-lvm"], volume, suppress_tmpdir=self.dry_run)
        # calculate where the datadirectory on the snapshot will be located
        rpath = relpath(datadir, getmount(datadir))
        snap_datadir = os.path.abspath(os.path.join(snapshot.mountpoint, rpath))
        # setup actions to perform at each step of the snapshot process
        setup_actions(
            snapshot=snapshot,
            config=self.config,
            client=self.client,
            snap_datadir=snap_datadir,
            spooldir=self.target_directory,
        )

        if self.dry_run:
            return _dry_run(self.target_directory, volume, snapshot, datadir)

        try:
            snapshot.start(volume)
        except CallbackFailuresError as exc:
            for callback, error in exc.errors:
                LOG.error("%s: %s", callback, error)
            raise BackupError("Error occurred during snapshot process. Aborting.")
        except LVMCommandError as exc:
            # Something failed in the snapshot process
            raise BackupError(str(exc))
        except BaseException as ex:
            LOG.debug(ex)

        return None
