"""
Generic command backup plugin
"""

import os
import shlex

from holland.core.backup import BackupError, BackupPlugin

CONFIGSPEC = """
[command]
command = string(default=None)
create-backup-data-dir = boolean(default=False)
""".splitlines()


class CommandPlugin(BackupPlugin):
    """Command plugin for Holland"""

    def __init__(self, name, config, target_directory, dry_run=False):
        super().__init__(name, config, target_directory, dry_run)
        self.config.validate_config(CONFIGSPEC)
        self.plugin_config = config["command"]
        self._validate_plugin_cfg()

    def _validate_plugin_cfg(self):
        if not self.plugin_config["command"]:
            raise BackupError("Command is not set")

    @property
    def backup_data_dir(self):
        """Return the backup data directory"""
        return os.path.join(self.target_directory, "backup_data")

    def estimate_backup_size(self):
        return 0

    def backup(self):
        """Execute the command specified in the config"""
        if self.dry_run:
            self.log.info("Running in dry-run mode.")

        cmd = self.plugin_config["command"]
        if "{backup_data_dir}" in cmd:
            cmd = cmd.replace("{backup_data_dir}", self.backup_data_dir)

        # Split command into list of arguments
        try:
            cmd_parts = shlex.split(cmd)
        except Exception as ex:
            raise BackupError("Invalid command syntax: %s" % ex) from ex

        if self.plugin_config["create-backup-data-dir"]:
            self.log.info("Creating backup directory: %s", self.backup_data_dir)
            if not self.dry_run:
                try:
                    os.makedirs(self.backup_data_dir, exist_ok=True)
                except OSError as ex:
                    raise BackupError(
                        "Failed to create backup directory: %s" % ex
                    ) from ex

        if self.dry_run:
            self.log.info("Dry run executing: %s", repr(cmd_parts))
            return

        rc, stdout, _ = self.run_command(
            cmd_parts,
            capture_output=True,
            redirect_stderr_to_stdout=True,
        )
        self.log.info("command output:\n%s", stdout)

        if rc != 0:
            raise BackupError("Command returned a non-zero exit code")
