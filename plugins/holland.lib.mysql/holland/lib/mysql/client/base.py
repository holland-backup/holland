"""MySQLdb.Connection wrappers"""

import sys
import re
import logging
import MySQLdb
import MySQLdb.connections

MySQLError = MySQLdb.MySQLError
ProgrammingError = MySQLdb.ProgrammingError
OperationalError = MySQLdb.OperationalError

LOG = logging.getLogger(__name__)

__all__ = [
    'connect',
    'MySQLClient',
    'PassiveMySQLClient',
    'AutoMySQLClient',
    'MySQLError',
    'ProgrammingError',
    'OperationalError',
]

def flatten_list(a_list):
    """Given a list of sequences, return a flattened list

    >>> flatten_list([['a', 'b', 'c'], ['e', 'f', 'j']])
    ['a', 'b', 'c', 'e', 'f', 'j']
    >>> flatten_list([['aaaa', 'bbbb'], 'b', 'cc'])
    ['aaaa', 'bbbb', 'b', 'cc']
    """
    # isinstance check to ensure we're not iterating over characters
    # in a string
    return sum([isinstance(item, (list, tuple)) and list(item) or [item]
                    for item in a_list], [])

class MySQLClient(object):
    """MySQLdb Helper

    Provides common functions for reading meta-data
    from and performing administrative functions on
    a MySQL server.

    This class also behave as a MySQLdb.Connection
    object and can be used to perform arbitrary queries
    using the Python dbapi.
    """

    SCOPE = ['GLOBAL', 'SESSION']

    def __init__(self, *args, **kwargs):
        """Create a new MySQLClient instance

        This is a simple wrapper for MySQLdb.connect(*args, **kwargs)

        :param args: args tuple to pass to MySQLdb.connect
        :param kwargs: kwargs dict to pass to MySQLdb.connect
        """
        self._connection = MySQLdb.connect(*args, **kwargs)

    def flush_tables(self):
        """Flush MySQL server table data to disk


        Runs FLUSH TABLES
        Also flushes the query cache and closes all
        open tables:

        http://dev.mysql.com/doc/refman/5.0/en/flush.html
        """
        cursor = self.cursor()
        cursor.execute('FLUSH TABLES')
        cursor.close()

    def flush_tables_with_read_lock(self):
        """Acquire MySQL server global read lock

        Runs FLUSH TABLES WITH READ LOCK
        """
        cursor = self.cursor()
        cursor.execute('FLUSH TABLES WITH READ LOCK')
        cursor.close()

    def unlock_tables(self):
        """Unlock any tables previously locked by this session

        Runs UNLOCK TABLES
        """
        cursor = self.cursor()
        cursor.execute('UNLOCK TABLES')
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
        sql = "SHOW TABLE STATUS FROM `%s`" % database.replace('`','``')
        cursor = self.cursor()
        try:
            cursor.execute(sql)
        except MySQLError, exc:
            LOG.error("MySQL reported an error while running %s. [%d] %s", 
                      sql, *exc.args)
            raise
        names = [info[0].lower() for info in cursor.description]
        result = []
        for row in cursor:
            row = dict(zip(names, row))
            row['database'] = database
            row['data_size'] = (row.pop('data_length') or 0)
            row['index_size'] = (row.pop('index_length') or 0)
            # coerce null engine to 'view' as necessary
            if row['engine'] is None:
                if row['comment'] == 'VIEW':
                    row['engine'] = 'VIEW'
                else:
                    row['engine'] = ''
                    if 'references invalid table' in (row['comment'] or ''):
                        LOG.warning("Invalid view %s.%s: %s", 
                                    row['database'], row['name'],
                                    row['comment'] or '')
                    if 'Incorrect key file' in (row['comment'] or ''):
                        LOG.warning("Invalid table %s.%s: %s",
                                    row['database'], row['name'],
                                    row['comment'] or '')
            row['is_transactional'] = row['engine'].lower() in ['view', 
                                                                'innodb']
            for key in row.keys():
                valid_keys = [
                    'database',
                    'name',
                    'data_size',
                    'index_size',
                    'engine',
                    'is_transactional'
                ]
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
        sql = ("SELECT TABLE_SCHEMA AS `database`, "
               "          TABLE_NAME AS `name`, "
               "          COALESCE(DATA_LENGTH, 0) AS `data_size`, "
               "          COALESCE(INDEX_LENGTH, 0) AS `index_size`, "
               "          COALESCE(ENGINE, 'view') AS `engine`, "
               "          (TRANSACTIONS = 'YES' OR ENGINE IS NULL) AS `is_transactional` "
               "FROM INFORMATION_SCHEMA.TABLES "
               "LEFT JOIN INFORMATION_SCHEMA.ENGINES USING (ENGINE) "
               "WHERE TABLE_SCHEMA = %s")
        cursor = self.cursor()
        cursor.execute(sql, (database))
        names = [info[0] for info in cursor.description]
        all_rows = cursor.fetchall()
        result = [dict(zip(names, row)) for row in all_rows]
        cursor.close()
        return result

    def show_table_metadata(self, database):
        """Iterate over the table metadata for the specified database.

        :param database: database to extract metadata from
        :returns: list of dicts, one dict per table
        """
        if self.server_version() < (5,1):
            return self._show_table_metadata50(database)
        else:
            return self._show_table_metadata51(database)

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
        sql = "SHOW %sTABLES FROM `%s`" % \
            (['', 'FULL '][int(full)],
             database.replace('`','``'))
        cursor = self.cursor()
        cursor.execute(sql)
        try:
            if full:
                return [(table, kind) for table, kind in cursor]
            else:
                return [table for table in cursor]
        finally:
            cursor.close()

    def show_table_status(self, database):
        """SHOW TABLE STATUS

        :param database: database to extract table status from
        :returns: list of tuples
        """
        sql = "SHOW TABLE STATUS"
        cursor = self.cursor()
        cursor.execute(sql)
        try:
            return [row for row in cursor]
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
        database = database.replace('`', '``')
        table = table.replace('`', '``')
        cursor = self.cursor()
        if cursor.execute(sql % (database, table)):
            return cursor.fetchone()[1]
        cursor.close()

    def show_slave_status(self):
        """Fetch MySQL slave status

        :returns: slave status dict
        """
        sql = "SHOW SLAVE STATUS"
        cursor = self.cursor()
        cursor.execute(sql)
        keys = [col[0].lower() for col in cursor.description]
        slave_status = cursor.fetchone()
        cursor.close()

        if not slave_status:
            return None
        else:
            return dict(zip(keys, slave_status))

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
        else:
            return dict(zip(keys, master_status))

    def start_slave(self):
        """Run START SLAVE on the connected MySQL instance"""
        sql = "START SLAVE"
        cursor = self.cursor()
        result = cursor.execute(sql)
        cursor.close()
        return result

    def stop_slave(self):
        """Run STOP SLAVE on the connected MySQL instance"""
        sql = "STOP SLAVE"
        cursor = self.cursor()
        result = cursor.execute(sql)
        cursor.close()
        return result

    def show_status(self, key, session=False):
        """Fetch MySQL server status"""
        scope = self.SCOPE[session]
        sql = 'SHOW %s STATUS LIKE ' % scope + '%s'
        cursor = self.cursor()
        cursor.execute(sql, (key,))
        key, value = cursor.fetchone()
        cursor.close()
        return value

    def show_variable(self, key, session=False):
        """Fetch MySQL server variable"""
        scope = self.SCOPE[session]
        sql = 'SHOW %s VARIABLES LIKE ' % scope + '%s'
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
        sql = "SET %(scope)s %(variable)s = %(value)r" % \
            { 'scope' : self.SCOPE[session],
              'variable' : key,
              'value' : value
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
        m = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if m:
            return tuple([int(v) for v in m.groups()])
        else:
            raise MySQLError("Could not match server version: %r" % version)

    def __getattr__(self, key):
        """Pass through to the underlying MySQLdb.Connection object"""
        return getattr(self._connection, key)


class PassiveMySQLClient(MySQLClient):
    """A client connection that defers the connection process until
    the connect method is called"""

    def __init__(self, *args, **kwargs):
        self._connection = None
        self._args = args
        self._kwargs = kwargs

    def connect(self):
        """Connect to MySQL using the connection parameters this instance
        was created with.

        :raises: `MySQLError`
        """
        self._connection = MySQLdb.connect(*self._args, **self._kwargs)

    def disconnect(self):
        """Disconnect this instance from MySQL"""
        try:
            if self._connection:
                self._connection.close()
        finally:
            self._connection = None


class AutoMySQLClient(PassiveMySQLClient):
    """A client connection that deferred the connection process until
    `connect()` is called or one of the standard `MySQLClient` methods
    is requested"""

    def __getattr__(self, key):
        if self._connection is None:
            getattr(MySQLdb.connections.Connection, key)
            LOG.info("Initiating connection to MySQL")
            self.connect()

        # ensure the connection is usable
        try:
            self._connection.ping()
        except MySQLError:
            LOG.info("Reconnecting to MySQL after failed ping")
            self.connect()

        return super(AutoMySQLClient, self).__getattr__(key)

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
    # what MySQLdb.connect expects
    # http://mysql-python.sourceforge.net/MySQLdb.html#mysqldb
    CNF_TO_MYSQLDB = {
        'user' : 'user', # same
        'password' : 'passwd', # weird
        'host' : 'host', # same
        'port' : 'port',
        'socket' : 'unix_socket',
        'ssl' : 'ssl',
        'compress' : 'compress'
    }

    args = {}
    for key in config:
        # skip undefined values
        if config[key] is None:
            continue
        # convert my.cnf parameters to what MySQLdb expects
        if key in CNF_TO_MYSQLDB:
            args[CNF_TO_MYSQLDB[key]] = config[key]
        else:
            LOG.warn("Skipping unknown parameter %s", key)
    # also, always use utf8
    return client_class(charset='utf8', **args)
