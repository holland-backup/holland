"""Utility functions to help out the mysql-lvm plugin"""
import copy
import errno
import logging
import os
import shutil
import tempfile

from holland.core.backup import BackupError
from holland.core.util.fmt import format_bytes
from holland.lib.lvm import Snapshot, getmount, parse_bytes
from holland.lib.mysql import MySQLClient, MySQLError, build_mysql_config, connect

LOG = logging.getLogger(__name__)


def connect_simple(config):
    """Create a MySQLClientConnection given a mysql:client config
    section from a holland mysql backupset
    """
    try:
        mysql_config = build_mysql_config(config)
        connection = connect(mysql_config["client"], MySQLClient)
        sanitized = copy.deepcopy(mysql_config)
        sanitized["client"]["password"] = "[REDACTED]"
        LOG.debug("mysql_config => %s", sanitized)
        connection.connect()
        return connection
    except MySQLError as exc:
        raise BackupError("[%d] %s" % exc.args)


def cleanup_tempdir(path):
    """Delete tmpdir created for mounting snapshot"""
    if os.path.exists(path):
        LOG.info("Removing temporary mountpoint %s", path)
        shutil.rmtree(path)


def build_snapshot(config, logical_volume, suppress_tmpdir=False):
    """Create a snapshot process for running through the various steps
    of creating, mounting, unmounting and removing a snapshot
    """
    snapshot_name = config["snapshot-name"] or logical_volume.lv_name + "_snapshot"
    extent_size = int(logical_volume.vg_extent_size)
    snapshot_size = config["snapshot-size"]
    if not snapshot_size:
        snapshot_size = min(
            int(logical_volume.vg_free_count),
            (int(logical_volume.lv_size) * 0.2) / extent_size,
            (15 * 1024 ** 3) / extent_size,
        )
        LOG.info(
            "Auto-sizing snapshot-size to %s (%d extents)",
            format_bytes(snapshot_size * extent_size),
            snapshot_size,
        )
        if snapshot_size < 1:
            raise BackupError(
                "Insufficient free extents on %s "
                "to create snapshot (free extents = %s)"
                % (logical_volume.device_name(), logical_volume.vg_free_count)
            )
    else:
        try:
            _snapshot_size = snapshot_size
            snapshot_size = parse_bytes(snapshot_size) / extent_size
            LOG.info(
                "Using requested snapshot-size %s rounded by extent-size %s to %s.",
                _snapshot_size,
                format_bytes(extent_size),
                format_bytes(snapshot_size * extent_size),
            )
            if snapshot_size < 1:
                raise BackupError(
                    "Requested snapshot-size (%s) is less than 1 extent" % _snapshot_size
                )
            if snapshot_size > int(logical_volume.vg_free_count):
                LOG.info(
                    "Snapshot size requested %s, but only %s available.",
                    config["snapshot-size"],
                    format_bytes(int(logical_volume.vg_free_count) * extent_size, precision=4),
                )
                LOG.info(
                    "Truncating snapshot-size to %d extents (%s)",
                    int(logical_volume.vg_free_count),
                    format_bytes(int(logical_volume.vg_free_count) * extent_size, precision=4),
                )
                snapshot_size = int(logical_volume.vg_free_count)
        except ValueError as exc:
            raise BackupError("Problem parsing snapshot-size %s" % exc)

    mountpoint = config["snapshot-mountpoint"]
    tempdir = False
    if not mountpoint:
        tempdir = True
        if not suppress_tmpdir:
            mountpoint = tempfile.mkdtemp()
    else:
        try:
            os.makedirs(mountpoint)
            LOG.info("Created mountpoint %s", mountpoint)
        except OSError as exc:
            # silently ignore if the mountpoint already exists
            if exc.errno != errno.EEXIST:  # pylint: disable=no-member
                raise BackupError("Failure creating snapshot mountpoint: %s" % str(exc))
    snapshot = Snapshot(snapshot_name, int(snapshot_size), mountpoint)
    if tempdir:
        snapshot.register("finish", lambda *args, **kwargs: cleanup_tempdir(mountpoint))
    return snapshot


def log_final_snapshot_size(event, snapshot):
    """Log the final size of the snapshot before it is removed"""
    snapshot.reload()
    snap_percent = float(snapshot.snap_percent) / 100
    snap_size = float(snapshot.lv_size)
    LOG.info(
        "Final LVM snapshot size for %s is %s during %s",
        snapshot.device_name(),
        format_bytes(snap_size * snap_percent),
        event,
    )


def _dry_run(target_directory, volume, snapshot, datadir):
    """Implement dry-run for LVM snapshots."""
    LOG.info(
        volume.vg_name,
        volume.lv_name,
        volume.vg_name,
        snapshot.name,
        format_bytes(snapshot.size * int(volume.vg_extent_size)),
    )
    LOG.info("* Would mount on %s", snapshot.mountpoint or "generated temporary directory")
    if getmount(target_directory) == getmount(datadir):
        LOG.error(
            "Backup directory %s is on the same filesystem as the source logical volume %s.",
            target_directory,
            volume.device_name(),
        )
        LOG.error(
            "This will result in very poor performance and "
            "has a high potential for failed backups."
        )
        raise BackupError("Improper backup configuration for LVM.")
