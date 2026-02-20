"""Command Line Interface"""

import codecs
import logging
import os
from copy import deepcopy

from holland.backup.mariadb_dump.base import start
from holland.backup.mariadb_dump.command import MariaDBDump, MariaDBDumpError
from holland.backup.mariadb_dump.mock import MockEnvironment
from holland.core.backup import BackupError
from holland.lib.common.compression import (
    COMPRESSION_CONFIG_STRING,
    lookup_compression,
    open_stream,
)
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
from holland.lib.mysql.client.base import MYSQL_CLIENT_CONFIG_STRING
from holland.lib.mysql.option import build_mysql_config, write_options
from holland.lib.mysql.util import parse_size
from holland.lib.common.util import get_cmd_path

LOG = logging.getLogger(__name__)

# We validate our config against the following spec
CONFIGSPEC = (
    """
[mariadb-dump]
extra-defaults      = boolean(default=no)
executable          = string(default=mariadb-dump)
lock-method         = option('flush-lock', 'lock-tables', 'single-transaction', 'auto-detect', 'none', default='auto-detect') # pylint: disable=line-too-long
databases           = force_list(default=list('*'))
exclude-databases   = force_list(default=list())
tables              = force_list(default=list("*"))
exclude-tables      = force_list(default=list())
engines             = force_list(default=list("*"))
exclude-engines     = force_list(default=list())
exclude-invalid-views = boolean(default=no)
flush-logs          = boolean(default=no)
flush-privileges    = boolean(default=yes)
dump-routines       = boolean(default=yes)
dump-events         = boolean(default=yes)
dump-history        = boolean(default=no)
order-by-size       = boolean(default=no)
stop-slave          = boolean(default=no)
bin-log-position    = boolean(default=no)
max-allowed-packet  = string(default=128M)
file-per-database   = boolean(default=yes)
arg-per-database    = string(default={})
additional-options  = force_list(default=list())
estimate-method     = string(default='plugin')
"""
    + MYSQL_CLIENT_CONFIG_STRING
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


class MariaDBDumpPlugin:
    """mariadb-dump Backup Plugin interface for Holland"""

    CONFIGSPEC = CONFIGSPEC

    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.config.validate_config(self.CONFIGSPEC)  # -> ValidationError

        # Setup a discovery shell to find schema items
        # This will iterate over items during the estimate
        # or backup phase, which will call schema.refresh()
        self.schema = MySQLSchema()
        config = self.config["mariadb-dump"]
        self.schema.add_database_filter(include_glob(*config["databases"]))
        self.schema.add_database_filter(exclude_glob(*config["exclude-databases"]))

        self.schema.add_table_filter(include_glob_qualified(*config["tables"]))
        self.schema.add_table_filter(exclude_glob_qualified(*config["exclude-tables"]))
        self.schema.add_engine_filter(include_glob(*config["engines"]))
        self.schema.add_engine_filter(exclude_glob(*config["exclude-engines"]))

        self.mysql_config = build_mysql_config(self.config["mysql:client"])
        self.client = connect(self.mysql_config["client"])

        self.mock_env = None

    def estimate_backup_size(self):
        """Estimate the size of the backup this plugin will generate"""

        LOG.info("Estimating size of mariadb-dump backup")
        estimate_method = self.config["mariadb-dump"]["estimate-method"]

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
            try:
                self.client.connect()
            except Exception as ex:
                LOG.error("Failed to connect to database")
                LOG.debug("%s", ex)
                raise BackupError("MariaDB Error %s" % ex)
            try:
                self.schema.refresh(db_iter=db_iter, tbl_iter=tbl_iter)
            except MySQLError as exc:
                LOG.error("Failed to estimate backup size")
                LOG.debug("[%d] %s", *exc.args)
                raise BackupError("MariaDB Error [%d] %s" % exc.args)
            return float(sum([db.size for db in self.schema.databases]))
        finally:
            self.client.disconnect()

    def _fast_refresh_schema(self):
        # determine if we can skip expensive table metadata lookups entirely
        # and just worry about finding database names
        # However, with lock-method=auto-detect we must look at table engines
        # to determine what lock method to use
        config = self.config["mariadb-dump"]
        fast_iterate = (
            config["lock-method"] != "auto-detect"
            and not config["exclude-invalid-views"]
        )

        try:
            db_iter = DatabaseIterator(self.client)
            tbl_iter = SimpleTableIterator(self.client, record_engines=True)
            try:
                self.client.connect()
                self.schema.refresh(
                    db_iter=db_iter, tbl_iter=tbl_iter, fast_iterate=fast_iterate
                )
            except MySQLError as exc:
                LOG.debug("MariaDB error [%d] %s", exc_info=True, *exc.args)
                raise BackupError("MariaDB Error [%d] %s" % exc.args)
        finally:
            self.client.disconnect()

    def backup(self):
        """Run a MariaDB backup"""
        if self.schema.timestamp is None:
            self._fast_refresh_schema()

        try:
            self.client = connect(self.mysql_config["client"])
        except Exception as ex:
            LOG.debug("%s", ex)
            raise BackupError("Failed connecting to database'")

        if self.dry_run:
            self.mock_env = MockEnvironment()
            self.mock_env.replace_environment()
            LOG.info("Running in dry-run mode.")
            status = self.client.show_databases()
            if not status:
                raise BackupError("Failed to run 'show databases'")
        try:
            if self.config["mariadb-dump"]["stop-slave"]:
                slave_status = self.client.show_slave_status()
                if not slave_status:
                    raise BackupError(
                        "stop-slave enabled, but 'show slave status' failed"
                    )
                if slave_status and slave_status["slave_sql_running"] != "Yes":
                    raise BackupError(
                        "stop-slave enabled, but replication is not running"
                    )
                if not self.dry_run:
                    _stop_slave(self.client, self.config)
            elif self.config["mariadb-dump"]["bin-log-position"]:
                self.config["mysql:replication"] = {}
                repl_cfg = self.config["mysql:replication"]
                try:
                    master_info = self.client.show_master_status()
                    if master_info:
                        repl_cfg["master_log_file"] = master_info["file"]
                        repl_cfg["master_log_pos"] = master_info["position"]
                except MySQLError as exc:
                    raise BackupError(
                        "Failed to acquire master status [%d] %s" % exc.args
                    )
            self._backup()
        finally:
            if (
                self.config["mariadb-dump"]["stop-slave"]
                and "mysql:replication" in self.config
            ):
                _start_slave(self.client, self.config["mysql:replication"])
            if self.mock_env:
                self.mock_env.restore_environment()

    def _backup(self):
        """Real backup method.  May raise BackupError exceptions"""
        config = self.config["mariadb-dump"]
        # setup defaults_file with ignore-table exclusions
        defaults_file = os.path.join(self.target_directory, "my.cnf")
        write_options(self.mysql_config, defaults_file)
        if config["exclude-invalid-views"]:
            LOG.info("* Finding and excluding invalid views...")
            definitions_path = os.path.join(self.target_directory, "invalid_views.sql")
            exclude_invalid_views(self.schema, self.client, definitions_path)
        add_exclusions(self.schema, defaults_file)
        # find the path to the mariadb-dump command
        cmd_path = get_cmd_path(config["executable"])
        LOG.info("Using mariadb-dump executable: %s", cmd_path)
        # setup the mariadb-dump environment
        extra_defaults = config["extra-defaults"]
        try:
            mariadb_dump = MariaDBDump(
                defaults_file,
                cmd_path=cmd_path,
                extra_defaults=extra_defaults,
                mock_env=self.mock_env,
            )
        except MariaDBDumpError as exc:
            raise BackupError(str(exc))
        except Exception as ex:  # pylint: disable=W0703
            LOG.warning(ex)
        LOG.info("mariadb-dump version %s", mariadb_dump.version_str)
        bin_log_active = self.client.show_variable("log_bin") == "ON"
        try:
            mariadb_dump.set_options_from_config(config, bin_log_active=bin_log_active)
        except MariaDBDumpError as exc:
            raise BackupError(str(exc))

        os.mkdir(os.path.join(self.target_directory, "backup_data"))

        if (
            self.config["compression"]["method"] != "none"
            and self.config["compression"]["level"] > 0
        ):
            try:
                _, ext = lookup_compression(self.config["compression"]["method"])
            except OSError as exc:
                raise BackupError(
                    "Unable to load compression method '%s': %s"
                    % (self.config["compression"]["method"], exc)
                )
            LOG.info(
                "Using %s compression level %d with args %s",
                self.config["compression"]["method"],
                self.config["compression"]["level"],
                self.config["compression"]["options"],
            )
        else:
            LOG.info("Not compressing mariadb-dump output")
            ext = ""

        try:
            start(
                mariadb_dump=mariadb_dump,
                schema=self.schema,
                lock_method=config["lock-method"],
                file_per_database=config["file-per-database"],
                open_stream=self._open_stream,
                compression_ext=ext,
                arg_per_database=config["arg-per-database"],
            )
        except MariaDBDumpError as exc:
            raise BackupError(str(exc))

    def _open_stream(self, path, mode, method=None):
        """Open a stream through the holland compression api, relative to
        this instance's target directory
        """
        path = str(os.path.join(self.target_directory, "backup_data", path))
        config = deepcopy(self.config["compression"])
        if method:
            config["method"] = method
        stream = open_stream(path, mode, **config)
        return stream


def _stop_slave(client, config):
    """Stop MariaDB replication"""
    try:
        client.stop_slave(sql_thread_only=True)
        LOG.info("Stopped slave")
        config["mysql:replication"] = {}
        repl_cfg = config["mysql:replication"]
    except MySQLError as exc:
        raise BackupError("Failed to stop slave[%d]: %s" % exc.args)

    try:
        slave_info = client.show_slave_status()
        if slave_info:
            # update config with replication info
            log_file = slave_info["relay_master_log_file"]
            log_pos = slave_info["exec_master_log_pos"]
            repl_cfg["slave_master_log_file"] = log_file
            repl_cfg["slave_master_log_pos"] = log_pos
    except MySQLError as exc:
        raise BackupError("Failed to acquire slave status[%d]: %s" % exc.args)
    try:
        master_info = client.show_master_status()
        if master_info:
            repl_cfg["master_log_file"] = master_info["file"]
            repl_cfg["master_log_pos"] = master_info["position"]
    except MySQLError as exc:
        raise BackupError("Failed to acquire master status [%d] %s" % exc.args)

    LOG.info("MariaDB Replication has been stopped.")


def _start_slave(client, config=None):
    """Start MariaDB replication"""

    # Skip sanity check on slave coords if we didn't actually record any coords
    # This might happen if mariadb goes away between STOP SLAVE and SHOW SLAVE
    # STATUS.
    if config:
        try:
            slave_info = client.show_slave_status()
            if (
                slave_info
                and slave_info["exec_master_log_pos"] != config["slave_master_log_pos"]
            ):
                LOG.warning(
                    "Sanity check on slave status failed.  "
                    "Previously recorded %s:%d but currently found"
                    " %s:%d",
                    config["slave_master_log_file"],
                    config["slave_master_log_pos"],
                    slave_info["relay_master_log_file"],
                    slave_info["exec_master_log_pos"],
                )
                LOG.warning("ALERT! Slave position changed during backup!")
        except MySQLError as exc:
            LOG.warning("Failed to sanity check replication[%d]: %s", *exc.args)

        try:
            master_info = client.show_master_status()
            if master_info and master_info["position"] != config["master_log_pos"]:
                LOG.warning(
                    "Sanity check on master status failed.  "
                    "Previously recorded %s:%s but currently found"
                    " %s:%s",
                    config["master_log_file"],
                    config["master_log_pos"],
                    master_info["file"],
                    master_info["position"],
                )
                LOG.warning("ALERT! Binary log position changed during backup!")
        except MySQLError as exc:
            LOG.warning("Failed to sanity check master status. [%d] %s", *exc.args)

    try:
        client.start_slave()
        LOG.info("Restarted slave")
    except MySQLError as exc:
        raise BackupError("Failed to restart slave [%d] %s" % exc.args)


def exclude_invalid_views(schema, client, definitions_file):
    """Flag invalid MariaDB views as excluded to skip them during a mariadb-dump"""
    LOG.info("* Invalid and excluded views will be saved to %s", definitions_file)
    cursor = client.cursor()

    invalid_views = (
        "--\n-- DDL of Invalid Views\n-- Created automatically by Holland\n--\n"
    )

    for schema_db in schema.databases:
        if schema_db.excluded:
            continue
        for table in schema_db.tables:
            if table.excluded:
                continue
            if table.engine != "view":
                continue
            LOG.debug("Testing view %s.%s", schema_db.name, table.name)
            invalid_view = False
            try:
                cursor.execute(
                    "SHOW FIELDS FROM `%s`.`%s`" % (schema_db.name, table.name)
                )
                # check for missing definers that would bork
                # lock-tables
                for _, error_code, msg in client.show_warnings():
                    if error_code == 1449:  # ER_NO_SUCH_USER
                        raise MySQLError(error_code, msg)
            except MySQLError as exc:
                # 1356 = View references invalid table(s)...
                if exc.args[0] in (1356, 1142, 1143, 1449, 1267, 1271):
                    invalid_view = True
                else:
                    LOG.error(
                        "Unexpected error when checking invalid view %s.%s: [%d] %s",
                        schema_db.name,
                        table.name,
                        *exc.args
                    )
                    raise BackupError("[%d] %s" % exc.args)
            if invalid_view:
                LOG.warning(
                    "* Excluding invalid view `%s`.`%s`", schema_db.name, table.name
                )
                table.excluded = True
                view_definition = client.show_create_view(
                    schema_db.name, table.name, use_information_schema=True
                )
                if view_definition is None:
                    LOG.error(
                        "!!! Failed to retrieve view definition for `%s`.`%s`",
                        schema_db.name,
                        table.name,
                    )
                    LOG.warning(
                        "!!! View definition for `%s`.`%s` will not be included in this backup",
                        schema_db.name,
                        table.name,
                    )
                    continue

                LOG.info(
                    "* Saving view definition for `%s`.`%s`",
                    schema_db.name,
                    table.name,
                )
                invalid_views = (
                    invalid_views
                    + "--\n-- Current View: `%s`.`%s`\n--\n%s;\n"
                    % (
                        schema_db.name,
                        table.name,
                        view_definition,
                    )
                )
    with open(definitions_file, "w") as sqlf:
        sqlf.write(invalid_views)


def add_exclusions(schema, config):
    """Given a MySQLSchema add --ignore-table options in a [mariadb-dump]
    section for any excluded tables.

    """

    exclusions = []
    for schema_db in schema.databases:
        if schema_db.excluded:
            continue
        for table in schema_db.tables:
            if table.excluded:
                LOG.info("Excluding table %s.%s", table.database, table.name)
                exclusions.append("ignore-table = " + table.database + "." + table.name)

    if not exclusions:
        return

    try:
        my_cnf = codecs.open(config, "a", "utf8")
        print(file=my_cnf)
        print("[mariadb-dump]", file=my_cnf)
        for excl in exclusions:
            print(excl, file=my_cnf)
        my_cnf.close()
    except IOError:
        LOG.error("Failed to write ignore-table exclusions to %s", config)
        raise
