"""
Base class for mysqlsh plugins
"""

import os
import re

from holland.backup.mysqlsh.mysql import MySqlHelper
from holland.core.backup import BackupError, BackupPlugin
from holland.lib.util import get_cmd_path

from .config import MYSQLSH_SHARED_OPTIONS
from .utils import kebab_to_camel, parse_version


class MySqlShBase(BackupPlugin):
    """
    Base class for MySQL Shell backup plugins
    """

    CONFIGSPEC = None  # Subclasses must define this
    CONFIG_KEY = None  # Subclasses must define this

    def __init__(self, name, config, target_directory, dry_run=False):
        super().__init__(name, config, target_directory, dry_run)
        self.config.validate_config(self.CONFIGSPEC)
        self.plugin_config = self.config[self.CONFIG_KEY]
        self.mysql = MySqlHelper(self.config["mysql:client"], self.plugin_config)

        self.bin_path = self._get_bin_path()
        self.version = self._get_version()
        if parse_version(self.version) < (8, 0, 32):
            raise BackupError("mysqlsh version must be at least 8.0.32")

        self._validate_mysqlsh_options()

    def _validate_mysqlsh_options(self):
        """Validate the options for the backup plugin."""
        return

    def _get_bin_path(self):
        """Get the path to the mysqlsh executable."""
        if not self.plugin_config["executable"]:
            raise BackupError("mysqlsh executable not specified")
        return get_cmd_path(self.plugin_config["executable"])

    def _get_version(self):
        """Get the version of mysqlsh"""
        cmd = [self.bin_path, "--log-level=1", "--log-file=/dev/null", "--version"]
        rc, stdout, _ = self.run_command(
            cmd, capture_output=True, redirect_stderr_to_stdout=True
        )

        if rc != 0:
            raise BackupError("Failed to determine mysqlsh version: %s" % stdout)

        match = re.search(r"\b(\d+\.\d+\.\d+)\b", stdout)
        if match:
            self.log.info("mysqlsh version: %s", match.group(1))
            return match.group(1)

        raise BackupError(
            "Failed to determine mysqlsh version: No version found in output"
        )

    def _generate_named_args(self, options):
        """Return a list of named arguments from an options dict."""
        args = []
        for opt_name, metadata in options.items():
            if self.plugin_config[opt_name] == metadata.get(
                "default"
            ) and not metadata.get("always_show", False):
                continue
            if opt_name in ["strip-definers", "create-invisible-pks"]:
                args.append("--compatibility=%s" % (opt_name.replace("-", "_")))
                continue
            if opt_name == "bytes-per-chunk" and not self.plugin_config["chunking"]:
                continue
            args.append(
                "--%s=%s" % (kebab_to_camel(opt_name), self.plugin_config[opt_name])
            )
        return args

    def _get_pos_args(self):
        """Return a list of positional arguments for the backup command."""
        return []

    def _get_named_args(self):
        """Return a list of named arguments for the backup command."""
        return []

    def _generate_backup_cmd(self, defaults_file=None):
        """Generate the base backup command with common options"""
        defaults_param = (
            "--defaults-extra-file"
            if self.plugin_config["extra-defaults"]
            else "--defaults-file"
        )
        cmd = [
            self.bin_path,
            "%s=%s" % (defaults_param, defaults_file),
            "--log-file=%s/mysqlsh.log" % (self.target_directory),
            "--log-level=%s" % (self.plugin_config["log-level"]),
            "--",
            "util",
            self.CONFIG_KEY.replace("mysqlsh-", ""),
        ]

        # Add plugin specific positional arguments
        cmd.extend(self._get_pos_args())
        if self.dry_run:
            cmd.append("--dryRun=True")

        # Add plugin specific named arguments
        cmd.extend(self._get_named_args())

        # Add shared options
        cmd.extend(self._generate_named_args(MYSQLSH_SHARED_OPTIONS))

        # Add extra-args staight from the config
        if self.plugin_config["additional-options"]:
            cmd.extend(self.plugin_config["additional-options"])
        return cmd

    @property
    def local_output_url(self):
        """Generate the local output URL when dump-to-remote is not enabled."""
        return os.path.join(self.target_directory, "backup_data")

    @property
    def output_url(self):
        """Get the appropriate output URL based on configuration."""
        # This just returns the local output URL for now. We can hook into here
        # should we enable support for remote dumps.
        return self.local_output_url

    def estimate_backup_size(self):
        """Estimate the size of the backup this plugin will generate"""

        self.log.info("Estimating size of %s backup", self.CONFIG_KEY)
        return self.mysql.estimate_schema_size()

    def backup(self):
        """Run mysqlsh backup"""
        if self.dry_run:
            self.log.info("Running in dry-run mode.")

        self.mysql.run_backup_prep()
        try:
            if self.plugin_config["stop-slave"]:
                # Validate slave is running before stopping it
                self.mysql.validate_slave_status()
                if not self.dry_run:
                    self.mysql.stop_slave()

                    # Ensure mysql:replication exists in the config to ensure we run the
                    # start_slave later regardless if we fail to get the replication config
                    self.config["mysql:replication"] = {}
                    self.config["mysql:replication"] = (
                        self.mysql.get_slave_replication_cfg()["slave_master_log_file"]
                    )
                    self.log.info("MySQL replication has been stopped.")
            elif self.plugin_config["bin-log-position"]:
                self.config["mysql:replication"] = self.mysql.get_master_data()

            defaults_file = self.mysql.write_defaults_file(self.target_directory)
            cmd = self._generate_backup_cmd(defaults_file=defaults_file)
            rc, stdout, _ = self.run_command(
                cmd, capture_output=True, redirect_stderr_to_stdout=True
            )
            self.log.info("mysqlsh command output:\n%s", stdout)
            if rc != 0:
                raise BackupError("Failed to backup instance")

        finally:
            if (
                not self.dry_run
                and self.plugin_config["stop-slave"]
                and "mysql:replication" in self.config
            ):
                self.mysql.start_slave(repl_config=self.config["mysql:replication"])
