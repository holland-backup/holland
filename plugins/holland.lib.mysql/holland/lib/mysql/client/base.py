"""pymysql.Connection wrappers"""

import logging
import re
from textwrap import dedent
from warnings import filterwarnings

import pkg_resources
import pymysql
import pymysql.connections
from pymysql import MySQLError, OperationalError, ProgrammingError

LOG = logging.getLogger(__name__)

filterwarnings("ignore", category=pymysql.Warning)

__all__ = [
    "connect",
    "MySQLClient",
    "AutoMySQLClient",
    "MySQLError",
    "ProgrammingError",
    "OperationalError",
]

MYSQL_CLIENT_CONFIG_STRING = """
[mysql:client]
defaults-extra-file = force_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(min=0, default=None)
"""


def flatten_list(a_list):
    """Given a list of sequences, return a flattened list

    >>> flatten_list([['a', 'b', 'c'], ['e', 'f', 'j']])
    ['a', 'b', 'c', 'e', 'f', 'j']
    >>> flatten_list([['aaaa', 'bbbb'], 'b', 'cc'])
    ['aaaa', 'bbbb', 'b', 'cc']
    """
    # isinstance check to ensure we're not iterating over characters
    # in a string
    return sum(
        [isinstance(item, (list, tuple)) and list(item) or [item] for item in a_list],
        [],
    )


class MySQLClient(object):
    """pymysql Helper

    Provides common functions for reading meta-data
    from and performing administrative functions on
    a MySQL server.

    This class also behave as a pymysql.Connection
    object and can be used to perform arbitrary queries
    using the Python dbapi.

    If the passive kwarg is set to False, it will not defer connection until
    the connect method is called. The default is True.
    """

    SCOPE = ["GLOBAL", "SESSION"]

    def __init__(self, *args, **kwargs):
        """Create a new MySQLClient instance

        This is a simple wrapper for pymysql.connect(*args, **kwargs)

        :param args: args tuple to pass to pymysql.connect
        :param kwargs: kwargs dict to pass to pymysql.connect
        """
        passive = kwargs.pop("passive", True)
        self._connection = None
        self._args = args
        self._kwargs = kwargs
        if not passive:
            self.connect()

    def connect(self):
        """Connect to MySQL using the connection parameters this instance
        was created with.

        :raises: `MySQLError`
        """
        self._connection = pymysql.connect(*self._args, **self._kwargs)

    def disconnect(self):
        """Disconnect this instance from MySQL"""
        try:
            if self._connection:
                self._connection.close()
        finally:
            self._connection = None

    def flush_tables(self):
        """Flush MySQL server table data to disk


        Runs FLUSH TABLES
        Also flushes the query cache and closes all
        open tables:

        http://dev.mysql.com/doc/refman/5.0/en/flush.html
        """
        cursor = self.cursor()
        cursor.execute("FLUSH /*!40101 LOCAL */ TABLES")
        cursor.close()

    def flush_tables_with_read_lock(self):
        """Acquire MySQL server global read lock

        Runs FLUSH TABLES WITH READ LOCK
        """
        cursor = self.cursor()
        cursor.execute("FLUSH TABLES WITH READ LOCK")
        cursor.close()

    def unlock_tables(self):
        """Unlock any tables previously locked by this session

        Runs UNLOCK TABLES
        """
        cursor = self.cursor()
        cursor.execute("UNLOCK TABLES")
        cursor.close()

    def show_databases(self):
        """List available databases

        :returns: list of database names
        """
        sql = "SHOW DATABASES"
        cursor = self.cursor()
        cursor.execute(sql)
        # Flatten the list of lists containing the database names
        db_list = flatten_list(cursor.fetchall())
        cursor.close()
        return db_list

    def _show_table_metadata50(self, database):
        """MySQL 5.0 (and below) implement of show_table_metadata()

        This version uses SHOW TABLE STATUS and pulls out useful metadata
        :param database: database to extract metadata from
        :returns: list of dictionaries, one dictionary per table
        """
        sql = "SHOW TABLE STATUS FROM `%s`" % database.replace("`", "``")
        cursor = self.cursor()
        try:
            cursor.execute(sql)
        except MySQLError as exc:
            LOG.error("MySQL reported an error while running %s. [%d] %s", sql, *exc.args)
            raise
        names = [info[0].lower() for info in cursor.description]
        result = []
        for row in cursor:
            row = dict(list(zip(names, row)))
            row["database"] = database
            row["data_size"] = row.pop("data_length") or 0
            row["index_size"] = row.pop("index_length") or 0
            # coerce null engine to 'view' as necessary
            if row["engine"] is None:
                row["engine"] = "view"
                comment = row.get("comment", "")
                if "references invalid table" in comment:
                    LOG.warning("Invalid view %s.%s: %s", row["database"], row["name"], comment)
                if "Incorrect key file" in comment:
                    LOG.warning("Invalid table %s.%s: %s", row["database"], row["name"], comment)
            else:
                row["engine"] = row["engine"].lower()
            for key in list(row.keys()):
                valid_keys = ["database", "name", "data_size", "index_size", "engine"]
                if key not in valid_keys:
                    row.pop(key)
            result.append(row)
        cursor.close()
        return result

    def _show_table_metadata51(self, database):
        """MySQL 5.1+ implementation of show_table_metadata

        This version uses the information schema primarily so
        we can identify whether an engine is transactional by
        examining the INFORMATION_SCHEMA.ENGINES table.

        :param database: database to extract metadata from
        :returns: list of dictionaries, one dictionary per table
        """
        sql = (
            "SELECT TABLE_SCHEMA AS `database`, "
            "          TABLE_NAME AS `name`, "
            "          COALESCE(DATA_LENGTH, 0) AS `data_size`, "
            "          COALESCE(INDEX_LENGTH, 0) AS `index_size`, "
            "          LOWER(COALESCE(ENGINE, 'view')) AS `engine` "
            "FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = %s"
        )
        cursor = self.cursor()
        cursor.execute(sql, (database,))
        names = [info[0] for info in cursor.description]
        all_rows = cursor.fetchall()
        result = [dict(list(zip(names, row))) for row in all_rows]
        cursor.close()
        return result

    def show_table_metadata(self, database):
        """Iterate over the table metadata for the specified database.

        :param database: database to extract metadata from
        :returns: list of dicts, one dict per table
        """
        try:
            if self.server_version() < (5, 1):
                return self._show_table_metadata50(database)

            return self._show_table_metadata51(database)
        except MySQLError as exc:
            exc.args = (exc.args[0], exc.args[1].decode("utf8"))
            raise

    def show_tables(self, database, full=False):
        """List tables in the given database

        Runs SHOW TABLES FROM ``database`` and return a list of table
        names.

        If `full` is requested, then SHOW FULL TABLES FROM `database`
        will be run and a list of (name, kind) tuples will be returned
        where `kind` is a string matching either 'BASE TABLE' for a normal
        table or 'VIEW' if a table is actually a view.

        :param database: Required.  database name to list tables from
        :param full: Optional. include table type n the results
        :returns: list of table names
        """
        sql = "SHOW %sTABLES FROM `%s`" % (
            ["", "FULL "][int(full)],
            database.replace("`", "``"),
        )
        cursor = self.cursor()
        cursor.execute(sql)
        try:
            return list(cursor)
        finally:
            cursor.close()

    def show_table_status(self, database=None):
        """SHOW TABLE STATUS

        :param database: database to extract table status from
        :returns: list of tuples
        """
        if database:
            sql = "SHOW TABLE STATUS FROM %s" % database
        else:
            sql = "SHOW TABLE STATUS"
        cursor = self.cursor()
        cursor.execute(sql)
        try:
            return list(cursor)
        finally:
            cursor.close()

    def show_create_view(self, schema, name, use_information_schema=True):
        """Attempt to retrieve the CREATE VIEW statement for a given view

        This method will return None if no view could be found or any of the
        view queries have failed.

        SHOW CREATE VIEW will fail if a view references a column that
        no longer exists.

        If SHOW CREATE VIEW fails, this method attempts to reconstruct the
        CREATE VIEW statement from INFORMATION_SCHEMA.VIEWS, as long as
        use_information_schema=True.  A view retrieved in this manner will
        be missing the ALGORITHM attribute which would otherwise be reported
        by SHOW CREATE VIEW.
        """
        cursor = self.cursor()
        try:
            try:
                if cursor.execute("SHOW CREATE VIEW `%s`.`%s`" % (schema, name)):
                    return cursor.fetchone()[1]
            except MySQLError:
                LOG.warning(
                    "!!! SHOW CREATE VIEW failed for `%s`.`%s`. "
                    "The view likely references columns that no "
                    "longer exist in the underlying tables.",
                    schema,
                    name,
                )
            if not use_information_schema:
                return None

            LOG.warning(
                "!!! Reconstructing view definition `%s`.`%s` from "
                "INFORMATION_SCHEMA.VIEWS.  This definition will not "
                "have an explicit ALGORITHM set.",
                schema,
                name,
            )
            try:
                sql = dedent(
                    """
                             SELECT CONCAT(
                                'CREATE DEFINER=', DEFINER,
                                ' SQL SECURITY ', SECURITY_TYPE,
                                ' VIEW ', TABLE_NAME,
                                ' AS ', VIEW_DEFINITION,
                                CASE
                                WHEN CHECK_OPTION <> 'NONE' THEN
                                    CONCAT(' WITH ',
                                           CHECK_OPTION,
                                           ' CHECK OPTION')
                                ELSE
                                    ''
                                END
                                )
                                FROM INFORMATION_SCHEMA.VIEWS
                                WHERE TABLE_SCHEMA = %s
                                AND TABLE_NAME = %s
                             """
                )
                if cursor.execute(sql, (schema, name)):
                    return cursor.fetchone()[0]
            except MySQLError as exc:
                LOG.debug(
                    "INFORMATION_SCHEMA.VIEWS(%s,%s) failed: [%d] %s ", schema, name, *exc.args
                )
            return None
        finally:
            cursor.close()

    def show_create_table(self, database, table):
        """Fetch DDL for a table

        Runs SHOW CREATE TABLE `database`.`table` and
        returns only the DDL portion

        :param database: database the table is in
        :param table: name of the table
        :raises: MySQLError, if the table does not exist
        :returns: DDL string for the given string
        """

        sql = "SHOW CREATE TABLE `%s`.`%s`"
        database = database.replace("`", "``")
        table = table.replace("`", "``")
        cursor = self.cursor()
        if cursor.execute(sql % (database, table)):
            return cursor.fetchone()[1]
        cursor.close()
        return None

    def show_slave_status(self):
        """Fetch MySQL slave status

        :returns: slave status dict
        """
        sql = "SHOW SLAVE STATUS"
        cursor = self.cursor()
        try:
            cursor.execute(sql)
            keys = [col[0].lower() for col in cursor.description]
            slave_status = cursor.fetchone()
            cursor.close()

            if not slave_status:
                return None
            return dict(list(zip(keys, slave_status)))
        finally:
            cursor.close()

    def show_master_status(self):
        """Fetch MySQL master status"""
        sql = "SHOW MASTER STATUS"
        cursor = self.cursor()
        cursor.execute(sql)
        keys = [col[0].lower() for col in cursor.description]
        master_status = cursor.fetchone()
        cursor.close()

        if not master_status:
            return None
        return dict(list(zip(keys, master_status)))

    def start_slave(self):
        """Run START SLAVE on the connected MySQL instance"""
        sql = "START SLAVE"
        cursor = self.cursor()
        result = cursor.execute(sql)
        cursor.close()
        return result

    def stop_slave(self, sql_thread_only=False):
        """Run STOP SLAVE on the connected MySQL instance"""
        sql = "STOP SLAVE"
        if sql_thread_only:
            sql += " SQL_THREAD"
        LOG.info("Issuing %s", sql)
        cursor = self.cursor()
        result = cursor.execute(sql)
        cursor.close()
        return result

    def show_status(self, key, session=False):
        """Fetch MySQL server status"""
        if session is not None:
            scope = self.SCOPE[session]
        else:
            # 4.1 support - GLOBAL/SESSION STATUS is not implemented
            scope = ""
        sql = "SHOW %s STATUS LIKE " % scope + "%s"
        cursor = self.cursor()
        cursor.execute(sql, (key,))
        key, value = cursor.fetchone()
        cursor.close()
        return value

    def show_variable(self, key, session=False):
        """Fetch MySQL server variable"""
        scope = self.SCOPE[session]
        sql = "SHOW %s VARIABLES LIKE " % scope + "%s"
        cursor = self.cursor()
        if cursor.execute(sql, (key,)):
            value = cursor.fetchone()[1]
        else:
            value = None
        cursor.close()
        return value

    def set_variable(self, key, value, session=True):
        """Set a MySQL server variable.

        This method defaults to setting the variable for the session
        rather than globally.
        """
        sql = "SET %(scope)s %(variable)s = %(value)r" % {
            "scope": self.SCOPE[session],
            "variable": key,
            "value": value,
        }
        cursor = self.cursor()
        cursor.execute(sql)
        cursor.close()
        return self.show_variable(key, session)

    def server_version(self):
        """
        server_version(self)
        returns a numeric tuple: major, minor, revision versions (respectively)
        """
        version = self.get_server_info()
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if match:
            return tuple((int(v) for v in match.groups()))

        raise MySQLError("Could not match server version: %r" % version)

    def __getattr__(self, key):
        """Pass through to the underlying pymysql.Connection object"""
        return getattr(self._connection, key)


class AutoMySQLClient(MySQLClient):
    """A client connection that deferred the connection process until
    `connect()` is called or one of the standard `MySQLClient` methods
    is requested"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, passive=True, **kwargs)

    def __getattr__(self, key):
        if self._connection is None:
            getattr(pymysql.connections.Connection, key)
            LOG.debug("Connected to MySQL")
            self.connect()

        # ensure the connection is usable
        try:
            self._connection.ping()
        except MySQLError:
            LOG.info("Reconnecting to MySQL after failed ping")
            self.connect()

        return MySQLClient.__getattr__(self, key)


def connect(config, client_class=AutoMySQLClient):
    """Create a MySQLClient object from a dict

    :param config: dict-like object containing zero or more of
                   the keys:
                    user
                    password
                    host
                    port
                    socket
                    ssl
                    compress
    :returns: `MySQLClient` instance
    """

    # map standard my.cnf parameters to
    # what pymysql.connect expects
    # https://pymysql.readthedocs.io/en/latest/modules/connections.html
    #    "socket": "unix_socket",

    args = {}
    for key, value in config.items():
        # skip undefined values
        if config.get(key) is None:
            continue

        if "socket" in key:
            key = "unix_socket"

        if "port" in key:
            args[key] = int(value)
        elif "password" in key:
            # Pass password to pymysql as bytes to
            # prevent encoding issues
            pymysql_version = pkg_resources.get_distribution("pymysql").version
            if int(pymysql_version.split(".")[0]) > 1:
                args[key] = value.decode("utf-8")
            else:
                LOG.debug("Using legacy password encoding, only ASCII characters are supported")
                args["passwd"] = value
        elif isinstance(value, bytes):
            args[key] = value.decode("utf-8")
        else:
            args[key] = value
    return client_class(charset="utf8", **args)
