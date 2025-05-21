"""
mysqlsh dump-instance plugin
"""

from .base import MySqlShBase
from .config import generate_configspec

MYSQLSH_INSTANCE_OPTIONS = {
    "users": {"type": "boolean", "default": True},
    "exclude-users": {"type": "force_list", "default": []},
    "include-users": {"type": "force_list", "default": []},
    "exclude-schemas": {"type": "force_list", "default": []},
    "include-schemas": {"type": "force_list", "default": []},
}

CONFIG_KEY = "dump-instance"
CONFIGSPEC = generate_configspec(CONFIG_KEY, MYSQLSH_INSTANCE_OPTIONS)


class MySqlShDumpInstance(MySqlShBase):
    """
    mysqlsh dump-instance plugin
    """

    CONFIGSPEC = CONFIGSPEC
    CONFIG_KEY = CONFIG_KEY

    def __init__(self, name, config, target_directory, dry_run=False):
        super().__init__(name, config, target_directory, dry_run)
        self.mysql.add_schema_filter(
            self.plugin_config["include-schemas"], exclude=False
        )
        self.mysql.add_schema_filter(
            self.plugin_config["exclude-schemas"], exclude=True
        )
        self.mysql.add_table_filter(self.plugin_config["include-tables"], exclude=False)
        self.mysql.add_table_filter(self.plugin_config["exclude-tables"], exclude=True)

    def _get_pos_args(self):
        return [self.output_url]

    def _get_named_args(self):
        return self._generate_named_args(MYSQLSH_INSTANCE_OPTIONS)
