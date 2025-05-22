"""
Helper class for MySQL specific operations.
"""

import logging
import os

from holland.core.backup import BackupError
from holland.lib.mysql import (
    DatabaseIterator,
    MetadataTableIterator,
    MySQLError,
    MySQLSchema,
    SimpleTableIterator,
    connect,
    exclude_glob,
    exclude_glob_qualified,
    include_glob,
    include_glob_qualified,
)
from holland.lib.mysql.option import build_mysql_config, write_options
from holland.lib.mysql.util import parse_size


class MySqlHelper:
    """
    Helper class for MySQL specific operations for mysqlsh backups.
    """

    def __init__(self, mysql_client_config, plugin_config=None, log=None):
        self.log = log or logging.getLogger(__name__)
        self.mysql_config = build_mysql_config(mysql_client_config)
        self.plugin_config = plugin_config or {}
        self.client = connect(self.mysql_config["client"])
        self.schema = MySQLSchema()

    def _get_mysql_error_msg(self, ex):
        code = ex.args[0] if len(ex.args) > 0 else "N/A"
        message = ex.args[1] if len(ex.args) > 1 else str(ex)
        return "MySQL error [%s]: %s" % (code, message)

    def write_defaults_file(self, target_directory):
        """Write the defaults file to the target directory."""
        file_path = os.path.join(target_directory, "my.cnf")
        write_options(self.mysql_config, file_path)
        return file_path

    def force_reconnect(self):
        """Force a reconnect to the MySQL server."""
        try:
            self.client = connect(self.mysql_config["client"])
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error reconnecting to MySQL: %s" % error_msg) from ex

    def get_master_data(self):
        """Get the master data from the MySQL server."""
        data = {}
        try:
            master_info = self.client.show_master_status()
            if master_info:
                data = {
                    "master_log_file": master_info["file"],
                    "master_log_pos": master_info["position"],
                }
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error determining master status: %s" % error_msg)
        return data

    def add_table_filter(self, tables, exclude=True):
        """Add table filter to the schema."""
        if not tables:
            return
        glob_func = exclude_glob_qualified if exclude else include_glob_qualified
        self.schema.add_table_filter(glob_func(*tables))

    def add_schema_filter(self, schemas, exclude=True):
        """Add schema filter to the schema."""
        if not schemas:
            return
        glob_func = exclude_glob if exclude else include_glob
        self.schema.add_database_filter(glob_func(*schemas))

    def estimate_schema_size(self):
        """Estimate the total size of databases in the schema."""

        estimate_method = self.plugin_config.get("estimate-method", "plugin")
        if estimate_method.startswith("const:"):
            try:
                return parse_size(estimate_method[6:])
            except ValueError as exc:
                raise BackupError(str(exc))

        if estimate_method != "plugin":
            raise BackupError("Invalid estimate-method '%s'" % estimate_method)
        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = MetadataTableIterator(self.client)
            self.client.connect()
            self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            sizes = []
            for db in self.schema.databases:
                self.log.debug("Database name: %s : size: %s", db.name, db.size)
                sizes.append(db.size)
            return float(sum(sizes))
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error estimating schema size: %s" % error_msg) from ex
        finally:
            self.client.disconnect()

    def fast_refresh_schema(self, fast_iterate=False):
        """Refresh schema metadata, potentially skipping expensive table lookups."""
        if self.schema.timestamp is not None:
            return
        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = SimpleTableIterator(self.client, record_engines=True)
            self.client.connect()
            self.schema.refresh(
                db_iter=db_iter, tbl_iter=tbl_iter, fast_iterate=fast_iterate
            )
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Failed to refresh schema: %s" % error_msg) from ex

        finally:
            self.client.disconnect()

    def start_slave(self, repl_config=None):
        """Start MySQL replication, with optional sanity checks against recorded_repl_config."""
        if repl_config:
            try:
                slave_info = self.client.show_slave_status()
                if (
                    slave_info
                    and slave_info["exec_master_log_pos"]
                    != repl_config["slave_master_log_pos"]
                ):
                    self.log.warning(
                        "Sanity check on slave status failed. Previously recorded %s:%s "
                        "but currently found %s:%s",
                        repl_config["slave_master_log_file"],
                        repl_config["slave_master_log_pos"],
                        slave_info["relay_master_log_file"],
                        slave_info["exec_master_log_pos"],
                    )
                    self.log.warning("ALERT! Slave position changed during backup!")

            except MySQLError as ex:
                error_msg = self._get_mysql_error_msg(ex)
                self.log.warning("Failed to sanity check replication: %s", error_msg)

            try:
                master_info = self.client.show_master_status()
                if (
                    master_info
                    and master_info["position"] != repl_config["master_log_pos"]
                ):
                    self.log.warning(
                        "Sanity check on master status failed. Previously recorded %s:%s "
                        "but currently found %s:%s",
                        repl_config["master_log_file"],
                        repl_config["master_log_pos"],
                        master_info["file"],
                        master_info["position"],
                    )
                    self.log.warning(
                        "ALERT! Binary log position changed during backup!"
                    )
            except MySQLError as ex:
                error_msg = self._get_mysql_error_msg(ex)
                self.log.warning(
                    "Failed to sanity check master status before starting: %s",
                    error_msg,
                )
        try:
            self.client.start_slave()
            self.log.info("Restarted slave")
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error starting slave: %s" % error_msg) from ex

    def validate_slave_status(self):
        """Validate the slave status."""
        slave_status = self.client.show_slave_status()
        if not slave_status:
            raise BackupError("stop-slave enabled, but 'show slave status' failed")
        if slave_status and slave_status["slave_sql_running"] != "Yes":
            raise BackupError("stop-slave enabled, but replication is not running")

    def stop_slave(self):
        """Stop MySQL replication and return master/slave status info."""
        try:
            self.client.stop_slave(sql_thread_only=True)
            self.log.info("Stopped slave")
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error stopping slave: %s" % error_msg) from ex

    def get_slave_replication_cfg(self):
        """Get the slave replication configuration."""
        repl_config = {}
        try:
            slave_info = self.client.show_slave_status()
            if slave_info:
                repl_config["slave_master_log_file"] = slave_info.get(
                    "relay_master_log_file"
                )
                repl_config["slave_master_log_pos"] = slave_info.get(
                    "exec_master_log_pos"
                )
        except MySQLError as ex:
            error_msg = self._get_mysql_error_msg(ex)
            raise BackupError("Error getting slave status: %s" % error_msg) from ex

        repl_config.update(self.get_master_data())
        return repl_config

    def run_backup_prep(self):
        """Run backup preparation steps."""
        # Refresh schema metadata, potentially skipping expensive table lookups
        self.fast_refresh_schema(fast_iterate=True)

        # Force a reconnect to the MySQL server
        self.force_reconnect()

        # Check if the databases are accessible
        status = self.client.show_databases()
        if not status:
            raise BackupError("Error: 'show databases' returned no results")
