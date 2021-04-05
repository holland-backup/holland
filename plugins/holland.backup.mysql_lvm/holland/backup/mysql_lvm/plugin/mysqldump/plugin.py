"""MySQL LVM snapshot backups"""

# pylint: disable=no-name-in-module
# pylint: disable=import-error

import logging
import os

from holland.backup.mysql_lvm.plugin.common import (
    _dry_run,
    build_snapshot,
    connect_simple,
)
from holland.backup.mysql_lvm.plugin.mysqldump.util import setup_actions
from holland.backup.mysqldump import MySQLDumpPlugin
from holland.core.backup import BackupError
from holland.lib.lvm import (
    CallbackFailuresError,
    LogicalVolume,
    LVMCommandError,
    getmount,
    relpath,
)

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
#Set mysql error log location. This can be helpful in debugging mysqld errorrs
#Note that the mysql user will need write premissions to the target location
log-error               = string(default=None)

""".splitlines()
    + MySQLDumpPlugin.CONFIGSPEC
)


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
        self.client = connect_simple(self.config["mysql:client"])
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
        datadir = os.path.realpath(self.client.show_variable("datadir"))
        LOG.info("Backing up %s via snapshot", datadir)
        # lookup the logical volume mysql's datadir sits on
        try:
            volume = LogicalVolume.lookup_from_fspath(datadir)
        except LookupError as exc:
            raise BackupError("Failed to lookup logical volume for %s: %s" % (datadir, str(exc)))
        except Exception as ex:
            raise BackupError("Failed to lookup logical volume for %s: %s" % (datadir, str(ex)))

        try:
            # create a snapshot manager
            snapshot = build_snapshot(
                self.config["mysql-lvm"], volume, suppress_tmpdir=self.dry_run
            )
            # calculate where the datadirectory on the snapshot will be located
            rpath = relpath(datadir, getmount(datadir))
            snap_datadir = os.path.abspath(os.path.join(snapshot.mountpoint or "/tmp", rpath))

            LOG.debug("Snap Datadir: %s", snap_datadir)
            # setup actions to perform at each step of the snapshot process
            setup_actions(
                snapshot=snapshot,
                config=self.config,
                client=self.client,
                datadir=snap_datadir,
                spooldir=self.target_directory,
                plugin=self.mysqldump_plugin,
            )
        except Exception as ex:
            raise BackupError(str(ex))

        if self.config["mysqldump"]["bin-log-position"]:
            LOG.warning("bin-log-position is not supported with mysqldump-lvm.")
            LOG.warning(
                "Replication status will be saved to the " "[mysql:replication] section in %s",
                self.config.filename,
            )
            self.config["mysqldump"]["bin-log-position"] = False

        if self.dry_run:
            _dry_run(self.target_directory, volume, snapshot, datadir)
            # do the normal mysqldump dry-run
            return self.mysqldump_plugin.backup()

        try:
            snapshot.start(volume)
        except CallbackFailuresError as exc:
            for callback, error in exc.errors:
                LOG.error("%s: %s", callback, error)
            raise BackupError("Error occurred during snapshot process. Aborting.")
        except LVMCommandError as exc:
            # Something failed in the snapshot process
            raise BackupError(str(exc))

        return None
