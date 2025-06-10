"""
Define how backup plugins will be called
"""

import errno
import logging
import os
import subprocess
import sys
import time

from holland.core.plugin import PluginLoadError, load_backup_plugin
from holland.core.spool import Backup
from holland.core.util.fmt import format_bytes, format_interval
from holland.core.util.path import directory_size, disk_free

MAX_SPOOL_RETRIES = 5

LOG = logging.getLogger(__name__)


class BackupError(Exception):
    """Error during a backup"""


class BackupPlugin:
    """
    Define a backup plugin
    """

    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.log = LOG

    def run_command(
        self,
        cmd,
        capture_output=False,
        stdout=None,
        stderr=None,
        redirect_stderr_to_stdout=False,
        preexec_fn=None,
        env=None,
    ):  # pylint: disable=too-many-arguments
        """Runs a command and optionally captures its output.

        Args:
            cmd (list): The command to run.
            capture_output (bool, optional): If True, captures stdout and stderr. Defaults to False.
            stdout (file, optional): Where to send stdout to. Used when capture_output is False.
            stderr (file, optional): Where to send stderr to. Used when capture_output is False.
            redirect_stderr_to_stdout (bool, optional): If True, redirects stderr to stdout.
            Defaults to False.
            preexec_fn (callable, optional): Callable to run before the child process is executed.
            to True for string commands. Defaults to None.
            env (dict, optional): Environment variables to use for the new process.

        Returns:
            int or tuple: The command's return code as an int if capture_output is False,
            or a tuple of (returncode, stdout, stderr) if capture_output is True.

        Raises:
            BackupError: If the command fails to execute.
            TypeError: If cmd is not a list.
        """
        if not isinstance(cmd, list):
            raise TypeError("cmd must be a list")

        if capture_output:
            out_fd = subprocess.PIPE
            err_fd = subprocess.STDOUT if redirect_stderr_to_stdout else subprocess.PIPE
        else:
            out_fd = stdout
            err_fd = stderr if not redirect_stderr_to_stdout else subprocess.STDOUT
        try:
            self.log.info("Executing: %s", repr(cmd))
            p = subprocess.Popen(
                cmd,
                stdout=out_fd,
                stderr=err_fd,
                shell=False,
                env=env,
                universal_newlines=True,
                preexec_fn=preexec_fn,
            )
            if capture_output:
                stdout, stderr = p.communicate()
                return p.returncode, stdout, stderr

            return p.wait()

        except OSError as ex:
            raise BackupError("Failed to execute command: %s" % str(ex)) from ex

    def estimate_backup_size(self):
        """
        placeholder
        """
        raise NotImplementedError()

    def backup(self):
        """
        placeholder
        """
        raise NotImplementedError()


def load_plugin(name, config, path, dry_run):
    """
    Method to load plugins
    """
    try:
        plugin_cls = load_backup_plugin(config["holland:backup"]["plugin"])
    except KeyError:
        raise BackupError("No plugin defined for backupset '%s'." % name)
    except PluginLoadError as exc:
        raise BackupError(str(exc))

    try:
        return plugin_cls(name=name, config=config, target_directory=path, dry_run=dry_run)
    # commenting out the below in case we actually want to handle this one day
    # except (KeyboardInterrupt, SystemExit):
    #     raise
    except Exception as exc:
        LOG.debug("Error while initializing %r : %s", plugin_cls, exc, exc_info=True)
        raise BackupError(
            "Error initializing %s plugin: %s" % (config["holland:backup"]["plugin"], str(exc))
        )


class BackupRunner(object):
    """
    Run backup
    """

    def __init__(self, spool):
        self.spool = spool
        self._registry = {}

    def register_cb(self, event, callback):
        """
        create callback
        """
        self._registry.setdefault(event, []).append(callback)

    def apply_cb(self, event, *args, **kwargs):
        """
        Catch Callback
        """
        for callback in self._registry.get(event, []):
            try:
                callback(event, *args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                raise BackupError(str(sys.exc_info()[1]))

    def backup(self, name, config, dry_run=False):
        """Run a backup for the named backupset using the provided
        configuration

        :param name: name of the backupset
        :param config: dict-like object providing the backupset configuration

        :raises: BackupError if a backup fails
        """
        for i in range(MAX_SPOOL_RETRIES):
            try:
                spool_entry = self.spool.add_backup(name)
                break
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise BackupError("Failed to create spool: %s" % exc)
                LOG.debug("Failed to create spool.  Retrying in %d seconds.", i + 1)
                time.sleep(i + 1)
        else:
            raise BackupError("Failed to create a new backup directory for %s" % name)

        spool_entry.config.merge(config)
        spool_entry.validate_config()

        if dry_run:
            # always purge the spool
            self.register_cb("post-backup", lambda *args, **kwargs: spool_entry.purge())

        plugin = load_plugin(name, spool_entry.config, spool_entry.path, dry_run)

        spool_entry.config["holland:backup"]["start-time"] = time.time()
        spool_entry.flush()
        self.apply_cb("before-backup", spool_entry)
        spool_entry.config["holland:backup"]["failed"] = False

        try:
            estimated_size = self.check_available_space(plugin, spool_entry, dry_run)
            LOG.info(
                "Starting backup[%s] via plugin %s",
                spool_entry.name,
                spool_entry.config["holland:backup"]["plugin"],
            )
            plugin.backup()
        except KeyboardInterrupt:
            LOG.warning("Backup aborted by interrupt")
            spool_entry.config["holland:backup"]["failed"] = True
            raise
        except BaseException as ex:
            LOG.warning(ex)
            spool_entry.config["holland:backup"]["failed"] = True

        spool_entry.config["holland:backup"]["stop-time"] = time.time()
        if not dry_run and not spool_entry.config["holland:backup"]["failed"]:
            final_size = float(directory_size(spool_entry.path))
            LOG.info("Final on-disk backup size %s", format_bytes(final_size))
            if estimated_size > 0:
                LOG.info(
                    "%.2f%% of estimated size %s",
                    (final_size / estimated_size) * 100.0,
                    format_bytes(estimated_size),
                )

            spool_entry.config["holland:backup"]["on-disk-size"] = final_size
            spool_entry.flush()

        start_time = spool_entry.config["holland:backup"]["start-time"]
        stop_time = spool_entry.config["holland:backup"]["stop-time"]

        if spool_entry.config["holland:backup"]["failed"]:
            LOG.error("Backup failed after %s", format_interval(stop_time - start_time))
        else:
            LOG.info("Backup completed in %s", format_interval(stop_time - start_time))

        if dry_run:
            spool_entry.purge()

        if sys.exc_info() != (None, None, None) or spool_entry.config["holland:backup"]["failed"]:
            LOG.debug("sys.exc_info(): %r", sys.exc_info())
            self.apply_cb("failed-backup", spool_entry)
            raise BackupError("Failed backup: %s" % name)
        self.apply_cb("after-backup", spool_entry)

    def free_required_space(self, name, required_bytes, dry_run=False):
        """Attempt to free at least ``required_bytes`` of old backups from a backupset

        :param name: name of the backupset to free space from
        :param required_bytes: integer number of bytes required for the backupset path
        :param dry_run: if true, this will only generate log messages but won't actually free space
        :returns: bool; True if freed or False otherwise
        """
        LOG.info(
            "Insufficient disk space for adjusted estimated backup size: %s",
            format_bytes(required_bytes),
        )
        LOG.info("purge-on-demand is enabled. Discovering old backups to purge.")
        available_bytes = disk_free(os.path.join(self.spool.path, name))
        to_purge = {}
        for backup in self.spool.list_backups(name):
            backup_size = directory_size(backup.path)
            LOG.info("Found backup '%s': %s", backup.path, format_bytes(backup_size))
            available_bytes += backup_size
            to_purge[backup] = backup_size
            if available_bytes > required_bytes:
                break
        else:
            LOG.info(
                "Purging would only recover an additional %s", format_bytes(sum(to_purge.values()))
            )
            LOG.info(
                "Only %s total would be available, but the current backup requires %s",
                format_bytes(available_bytes),
                format_bytes(required_bytes),
            )
            return False

        purge_bytes = sum(to_purge.values())
        LOG.info(
            "Found %d backups to purge which will recover %s",
            len(to_purge),
            format_bytes(purge_bytes),
        )

        for backup in to_purge:
            if dry_run:
                LOG.info("Would purge: %s", backup.path)
            else:
                LOG.info("Purging: %s", backup.path)
                backup.purge()
        LOG.info(
            "%s now has %s of available space",
            os.path.join(self.spool.path, name),
            format_bytes(disk_free(os.path.join(self.spool.path, name))),
        )
        return True

    def historic_required_space(self, plugin, spool_entry, estimated_bytes_required):
        """
        Use size reported in 'newest' backup to predict backup size
        If this fails return a value less than zero and use the estimated-size-factor
        """
        config = plugin.config["holland:backup"]
        if not config["historic-size"]:
            return -1.0

        historic_size_factor = config["historic-size-factor"]

        old_backup_config = os.path.join(self.spool.path, spool_entry.backupset, "newest")
        if not os.path.exists(old_backup_config):
            LOG.debug("Missing backup.conf from last backup")
            return -1.0

        old_backup = Backup(old_backup_config, spool_entry.backupset, "newest")
        old_backup.load_config()

        if (
            old_backup.config["holland:backup"]["estimated-size-factor"]
            and old_backup.config["holland:backup"]["on-disk-size"]
        ):
            size_required = old_backup.config["holland:backup"]["on-disk-size"]
            old_estimate = old_backup.config["holland:backup"]["estimated-size"]
        else:
            LOG.debug(
                "The last backup's configuration was missing the \
                ['holland:backup']['on-disk-size'] or ['holland:backup']['estimated-size']"
            )
            return -1.0

        LOG.info(
            "Using Historic Space Estimate: Checking for information in %s",
            old_backup.config.filename,
        )
        LOG.info("Last backup used %s", format_bytes(size_required))
        if estimated_bytes_required > (old_estimate * historic_size_factor):
            LOG.warning(
                "The new backup estimate is at least %s times the size of "
                "the current estimate: %s > (%s * %s). Default back"
                " to 'estimated-size-factor'",
                historic_size_factor,
                format_bytes(estimated_bytes_required),
                format_bytes(old_estimate),
                historic_size_factor,
            )
            return -1.0

        LOG.debug(
            "The old and new backup estimate are roughly the same size, "
            "use old backup size for new size estimate"
        )
        return size_required * float(config["historic-estimated-size-factor"])

    def check_available_space(self, plugin, spool_entry, dry_run=False):
        """
        calculate available space before performing backup
        """
        available_bytes = disk_free(spool_entry.path)
        estimated_bytes_required = float(plugin.estimate_backup_size())
        spool_entry.config["holland:backup"]["estimated-size"] = estimated_bytes_required
        LOG.info("Estimated Backup Size: %s", format_bytes(estimated_bytes_required))

        adjusted_bytes_required = self.historic_required_space(
            plugin, spool_entry, estimated_bytes_required
        )

        config = plugin.config["holland:backup"]
        if adjusted_bytes_required < 0:
            adjustment_factor = float(config["estimated-size-factor"])
            adjusted_bytes_required = estimated_bytes_required * adjustment_factor

            if adjusted_bytes_required != estimated_bytes_required:
                LOG.info(
                    "Adjusting estimated size by %.2f to %s",
                    adjustment_factor,
                    format_bytes(adjusted_bytes_required),
                )
        else:
            adjustment_factor = float(config["historic-estimated-size-factor"])
            LOG.info(
                "Adjusting estimated size to last backup total * %s: %s",
                adjustment_factor,
                format_bytes(adjusted_bytes_required),
            )

        if available_bytes <= adjusted_bytes_required:
            if not (
                config["purge-on-demand"]
                and self.free_required_space(
                    spool_entry.backupset, adjusted_bytes_required, dry_run
                )
            ):
                msg = ("Insufficient Disk Space. %s required, " "but only %s available on %s") % (
                    format_bytes(adjusted_bytes_required),
                    format_bytes(available_bytes),
                    self.spool.path,
                )
                LOG.error(msg)
                if not dry_run:
                    raise BackupError(msg)
        return float(estimated_bytes_required)
