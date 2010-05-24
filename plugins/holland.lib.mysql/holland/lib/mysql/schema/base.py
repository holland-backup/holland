"""Summarize a MySQL Schema"""

import time
import logging

LOG = logging.getLogger(__name__)

class MySQLSchema(object):
    """A catalog summary of a MySQL Instance"""

    def __init__(self):
        self.databases = []
        self._database_filters = []
        self._table_filters = []
        self._engine_filters = []
        self.timestamp = None

    def excluded_tables(self):
        """Iterate over tables excluded in this schema"""
        for database in self.databases:
            for table in database:
                if table.excluded:
                    yield table
    excluded_tables = property(excluded_tables)

    def excluded_databases(self):
        """Iterate over databases excluded in this schema"""
        for database in self.databases:
            if database.excluded:
                yield database
    excluded_databases = property(excluded_databases)

    def add_database_filter(self, filterobj):
        """Add a database filter to this summary

        :param filterobj: a callable that returns True if a database
                          should be filtered by name
        :type filterobj: callable, such as `IncludeFilter` or `ExcludeFilter`
        """
        self._database_filters.append(filterobj)

    def add_table_filter(self, filterobj):
        """Add a table filter to this summary

        :param filterobj: a callable that returns True if a table
                          should be filtered by name
        :type filterobj: callable, such as `IncludeFilter` or `ExcludeFilter`
        """
        self._table_filters.append(filterobj)

    def add_engine_filter(self, filterobj):
        """Add an engine filter to this summary

        :param filterobj: a callable that returns True if a table
                          should be filtered by name
        :type filterobj: callable, such as `IncludeFilter` or `ExcludeFilter`
        """
        self._engine_filters.append(filterobj)

    def is_db_filtered(self, name):
        """Check if the database name is filtered by any database filters

        :param name: database name that should be checked against the list of
                     registered database filters.
        :type name: str
        :returns: True if the database named by `name` should be filtered
        """
        for _filter in self._database_filters:
            if _filter(name):
                return True

    def is_table_filtered(self, name):
        """Check if the table name is filtered by any table filters

        :param name: table name that should be checked against the list of
                     registered table filters.
        :type name: str
        :returns: True if the database named by `name` should be filtered
        """
        for _filter in self._table_filters:
            if _filter(name):
                return True

    def is_engine_filtered(self, name):
        """Check if the engine name is filtered by any engine filters

        :param name: engine name that should be checked against the list of
                     registered engine filters.
        :type name: str
        :returns: True if the table with the storage engine named by `name`
                  should be filtered
        """
        for _filter in self._engine_filters:
            if _filter(name):
                return True

    def refresh(self, db_iter, tbl_iter):
        """Summarize the schema by walking over the given database and table
        iterators

        :param db_iter: Required. A `DatabaseIterator` instance that will
                        provide an iterator instance when called with no
                        arguments. This iterator must yield `Database`
                        instances.
        :param tbl_iter: Required. A `TableIterator` instance that will return
                         provide an iterator instance when called with a
                         database name. This iterator must yield `Table`
                         instances from the requested database.
        """
        for database in db_iter():
            self.databases.append(database)
            if self.is_db_filtered(database.name):
                database.excluded = True
                continue
            for table in tbl_iter(database.name):
                if self.is_table_filtered(table.database + '.' + table.name):
                    table.excluded = True
                if self.is_engine_filtered(table.engine):
                    table.excluded = True
                database.add_table(table)
        self.timestamp = time.time()


class Database(object):
    """Representation of a MySQL Database

    Only the name an whether this database is
    excluded is recorded"""

    __slots__ = ('name', 'excluded', 'tables')

    def __init__(self, name):
        self.name = name
        self.tables  = []
        self.excluded = False

    def add_table(self, tableobj):
        """Add the table object to this database

        :param tableobj: `Table` instance that should be added to this
                         `Database` instance
        """
        self.tables.append(tableobj)

    def excluded_tables(self):
        """List tables associated with this database that are flagged as
        excluded"""
        for tableobj in self.tables:
            if tableobj.excluded:
                yield tableobj

    def is_transactional(self):
        """Check if this database is safe to dump in --single-transaction
        mode
        """
        for tableobj in self.tables:
            if not tableobj.is_transactional:
                return False

    def size(self):
        """Size of all non-excluded objects in this database

        :returns: int. sum of all data and indexes of tables that are not
                  excluded from this database
        """
        return sum([table.size for table in self.tables if not table.excluded])
    size = property(size)

    def __str__(self):
        return "Database(name=%r, table_count=%d, excluded=%r)" % \
                (self.name, len(self.tables), self.excluded)

    __repr__ = __str__

class Table(object):
    """Representation of a MySQL Table

    """
    __slots__ = ('database',
                 'name',
                 'data_size',
                 'index_size',
                 'engine',
                 'is_transactional',
                 'excluded',
                )

    def __init__(self, database,
                       name,
                       data_size,
                       index_size,
                       engine,
                       is_transactional):
        self.database = database
        self.name = name
        self.data_size = data_size
        self.index_size = index_size
        self.engine = engine
        self.is_transactional = is_transactional
        self.excluded = False

    def size(self):
        return self.data_size + self.index_size
    size = property(size)

    def __str__(self):
        return "%sTable(name=%r, data_size=%s, " + \
               "index_size=%s, engine=%s, txn=%s)" % \
                (self.excluded and "[EXCL]" or "",
                 self.name,
                 "%.2fMB" % (self.data_size / 1024.0**2),
                 "%.2fMB" % (self.index_size / 1024.0**2),
                 self.engine,
                 str(self.is_transactional)
                )

class DatabaseIterator(object):
    """Iterate over databases returns by a MySQLClient instance

    client must have a show_databases() method
    """
    def __init__(self, client):
        """Construct a new iterator to produce `Database` instances for the
        database requested by the __call__ method.

        :param client: `MySQLClient` instance to use to iterate over objects in
        the specified databasea
        """
        self.client = client

    def __call__(self):
        for name in self.client.show_databases():
            if name != 'information_schema':
                yield Database(name)


class TableIterator(object):
    """Iterate over tables returned by the client instance

    client must have a show_table_metadata(database_name) method
    """
    def __init__(self, client):
        """Construct a new iterator to produce `Table` instances for the
        database requested by the __call__ method.

        :param client: `MySQLClient` instance to use to iterate over objects in
        the specified database
        """
        self.client = client

    def __call__(self, database):
        raise NotImplementedError()

class MetadataTableIterator(TableIterator):
    """Iterate over SHOW TABLE STATUS in the requested database
    and yield Table instances
    """

    def __call__(self, database):
        for metadata in self.client.show_table_metadata(database):
            yield Table(**metadata)

import re

class SimpleTableIterator(MetadataTableIterator):
    """Iterator over tables returns by the client instance

    Unlike a MetadataTableIterator, this will not lookup the table size
    but rather just uses SHOW DATABASES/SHOW TABLES/SHOW CREATE TABLE

    SHOW CREATE TABLE is only used for engine lookup in MySQL 5.0.
    """
    
    ENGINE_PCRE = re.compile(r'^[)].*ENGINE=(\S+)', re.M)

    def __init__(self, client, record_engines=False):
        """Construct a new iterator to produce `Table` instances for the
        database requested by the __call__ method.

        :param client: `MySQLClient` instance to use to iterate over objects in
        the specified database
        """
        self.client = client
        self.record_engines = record_engines

    def _faster_mysql51_metadata(self, database):
        sql = ("SELECT TABLE_SCHEMA AS `database`, "
               "          TABLE_NAME AS `name`, "
               "          0 AS `data_size`, "
               "          0 AS `index_size`, "
               "          COALESCE(ENGINE, 'view') AS `engine`, "
               "          TRANSACTIONS = 'YES' AS `is_transactional` "
               "FROM INFORMATION_SCHEMA.TABLES "
               "JOIN INFORMATION_SCHEMA.ENGINES USING (ENGINE) "
               "WHERE TABLE_SCHEMA = %s")
        cursor = self.client.cursor()
        try:
            cursor.execute(sql, database)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _lookup_engine(self, database, table):
        ddl = self.client.show_create_table(database, table)
        match = self.ENGINE_PCRE.search(ddl)
        if match:
            return match.group(1)
        raise ValueError("Failed to lookup storage engine")

    def __call__(self, database):
        if self.client.server_version >= (5,1):
            for metadata in self._faster_mysql51_metadata():
                yield Table(**metadata)
        else:
            for table, kind in self.client.show_tables(database, full=True):
                metadata = [
                    ('database', database),
                    ('name', table),
                    ('data_size', 0),
                    ('index_size', 0),
                ]

                if kind == 'VIEW':
                    metadata.append(('engine', 'view'))
                    metadata.append(('is_transactional', 'yes'))
                else:
                    if self.record_engines:
                        engine = self._lookup_engine(database, table).lower()
                        metadata.append(('engine', engine))
                        metadata.append(('is_transactional', engine == 'innodb'))
                    else:
                        metadata.append(('engine', ''))
                        metadata.append(('is_transactional', False))
                yield Table(**dict(metadata))
