"""
mysqlsh dump-schemas plugin
"""

from holland.core.backup import BackupError

from .base import MySqlShBase
from .config import generate_configspec

MYSQLSH_INSTANCE_OPTIONS = {
    "schemas": {"type": "force_list", "default": []},
}

CONFIG_KEY = "mysqlsh-dump-schemas"
CONFIGSPEC = generate_configspec(CONFIG_KEY, MYSQLSH_INSTANCE_OPTIONS)


class MySqlShDumpSchemas(MySqlShBase):
    """
    mysqlsh dump-schemas plugin
    """

    CONFIGSPEC = CONFIGSPEC
    CONFIG_KEY = CONFIG_KEY

    def __init__(self, name, config, target_directory, dry_run=False):
        super().__init__(name, config, target_directory, dry_run)
        self.mysql.add_schema_filter(self.plugin_config["schemas"], exclude=False)
        self.mysql.add_table_filter(self.plugin_config["include-tables"], exclude=False)
        self.mysql.add_table_filter(self.plugin_config["exclude-tables"], exclude=True)

    def _validate_mysqlsh_options(self):
        """Validate the options for the dump-schemas plugin."""
        super()._validate_mysqlsh_options()

        if not self.plugin_config["schemas"]:
            raise BackupError("No schemas specified in backupset configuration")

    def _get_pos_args(self):
        return self.plugin_config["schemas"]

    def _get_named_args(self):
        return ["--outputUrl=%s" % self.output_url]
