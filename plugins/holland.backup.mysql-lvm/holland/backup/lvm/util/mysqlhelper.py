"""Helper class for MySQLdb"""

import logging
import MySQLdb
from MySQLdb import MySQLError

class MySQLHelper(object):
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
        self._connection = MySQLdb.connect(*args, **kwargs)

    def flush_tables(self):
        """Flush MySQL server table data to disk

        Also flushes the query cache and closes all
        open tables:

        http://dev.mysql.com/doc/refman/5.0/en/flush.html
        """
        cursor = self.cursor()
        cursor.execute('FLUSH TABLES')
        cursor.close()

    def flush_tables_with_read_lock(self):
        """Acquire MySQL server global read lock"""
        cursor = self.cursor()
        cursor.execute('FLUSH TABLES WITH READ LOCK')
        cursor.close()

    def unlock_tables(self):
        cursor = self.cursor()
        cursor.execute('UNLOCK TABLES')
        cursor.close()

    def status(self, key, session=False):
        """Fetch MySQL server status"""
        scope = self.SCOPE[session]
        sql = 'SHOW %s STATUS LIKE ' % scope + ' %s'
        cursor = self.cursor()
        cursor.execute(sql, (key,))
        key, value = cursor.fetchone()
        cursor.close()
        return value

    def variable(self, key, session=False):
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

    def show_master_status(self):
        sql = 'SHOW MASTER STATUS'
        cursor = self.cursor()
        if cursor.execute(sql):
            names = [info[0].lower() for info in cursor.description]
            status = dict(zip(names, cursor.fetchone()))
        else:
            status = None
        cursor.close()
        return status

    def show_slave_status(self):
        sql = 'SHOW SLAVE STATUS'
        cursor = self.cursor()
        if cursor.execute(sql):
            names = [info[0].lower() for info in cursor.description]
            status = dict(zip(names, cursor.fetchone()))
        else:
            status = None
        cursor.close()
        return status

    # Pass any undefined properties to the underlying
    # MySQLdb.Connection object
    def __getattr__(self, key):
        return getattr(self._connection, key)

def connect(*args, **kwargs):
    str_params = ','.join(['%s=%r' % (k, v) for k, v in kwargs.items()] +
                          list(args)
                         )
    logging.debug("mysql.connect(%s)", str_params)
    return MySQLHelper(*args, **kwargs)
