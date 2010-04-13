import re
import textwrap
import logging
import MySQLdb
from MySQLdb import OperationalError
from MySQLdb.constants.CLIENT import INTERACTIVE

__all__ = [
    'connect',
    'MySQLClient',
    'OperationalError',
    'ProgrammingError',
    'DatabaseError'
]

LOGGER = logging.getLogger(__name__)

class MySQLClient(object):
    def __init__(self, **kwargs):
        """
        Initialize a MySQLClient connections.  Keyword arguments are passed
        directly to MySQLdb.connect().  See MySQLdb for all known arguments.
        
        Possible Arguments:
        
        host        -- Name of host to connect to. 
        user        -- User to authenticate as. 
        passwd      -- Password to authenticate with.
        db          -- Database to use. 
        port        -- TCP port of MySQL server.
        unix_socket -- Location of UNIX socket.
        """
        self._conn = MySQLdb.connect(**kwargs)
    
    def quote_id(self, *args):
        """
        quote_id(self, *args)
        return a qualified list of quoted schema components
        ['test','bar`foo', 'column'] => "`test`.`bar``foo`.`columns`"
        """
        if not args: return None
        return '.'.join(map(lambda x: '`%s`' % x.replace('`','``'), args))

    def unquote_id(self, *args):
        result = []
        for arg in args:
            arg = arg[1:-1].replace('``', '`')
            result.append(arg)
        return result
 
    def quote(self, *args):
        """
        quote(self, *args)
        return a comma delimited string with each element in args quoted
        ['a', '\'b', 'c'] => "'a','''b','c'"
        """
        if not args: return None
        return ','.join(map(lambda x: "'%s'" % x.replace("'","''"), args))

    def show_databases(self):
        """
        Return a list of databases.
        """
        cursor = self.cursor()
        cursor.execute('SHOW DATABASES')
        result = [db for db, in cursor]
        cursor.close()
        return result
    
    def show_tables(self, db):
        """
        Return a list of tables for 'db'.
        
        Arguments:
        
        db -- The database name.
        """
        cursor = self.cursor()
        # probably should filter views
        cursor.execute('SHOW TABLES FROM %s' % self.quote_id(db))
        result = [tbl for tbl, in cursor]
        cursor.close()
        return result

    def show_table_status(self, db):
        """
        Return a the table status for 'db'.  Returns an iterable generator
        object.
        
        Arguments:
        
        db -- The database name.
        """
        cursor = self.cursor()
        cursor.execute('SHOW TABLE STATUS FROM %s' % self.quote_id(db))
        hdr = [d[0].lower() for d in cursor.description]
        while True:
            row = cursor.fetchone()
            if not row:
                break
            tbl_status = dict(zip(hdr, row))
            yield tbl_status
        cursor.close()

    def show_variable(self, name, session_only=False):
        """
        Returns the result of SHOW GLOBAL VARIABLIES LIKE '${name}' without
        any glob wild cards (only returns a single result (string)).
        
        Arguments:
        
        name         -- Name of the 'like' variable modifier
        session_only -- Boolean.  Only show session variables, rather than 
                        global.
        """
        cursor = self.cursor()
        if session_only:
            cursor.execute('SHOW SESSION VARIABLES LIKE %s', name)
        else:
            cursor.execute('SHOW GLOBAL VARIABLES LIKE %s', name)

        try:
            _, value = cursor.fetchone()
        except TypeError, e:
            value = None
        cursor.close()
        return value
    
    def show_variables_like(self, name, session_only=False):
        """
        Returns the result of SHOW GLOBAL VARIABLIES LIKE '%${name}%' with
        the glob wild card to return all matching variables.
        
        Arguments:
        
        name         -- Name of the 'like' variable modifier
        session_only -- Boolean.  Only show session variables, rather than 
                        global.
        """
        cursor = self.cursor()
        if session_only:
            cursor.execute('SHOW SESSION VARIABLES LIKE %s', name)
        else:
            cursor.execute('SHOW GLOBAL VARIABLES LIKE %s', name)

        variables = {}
        for row in cursor.fetchall():
            variables[row[0]] = row[1]
        cursor.close()
        return variables
    
    def set_variable(self, name, value, session=True):
        """
        Set a variable in the running server
        """
        cursor = self.cursor()
        name = self.quote_id(name)
        sql = 'SET ' + ['GLOBAL', 'SESSION'][session] + ' ' + name + ' = %s'
        cursor.execute(sql, value)
        if not session:
            LOGGER.debug("GLOBAL variable set: %s = %s" % (name, value))
        cursor.close()

    def set_wait_timeout(self, value):
        """
        Change the idle timeout for this connection.  This method is 
        deprecated, use MySQLClient.set_variable.
        
        If this connection is flagged as interactive interactive_timeout
        will be set, otherwise wait_timeout is set
        """
        if self.client_flag & INTERACTIVE:
            self.set_variable('interactive_timeout', value)
        else:
            self.set_variable('wait_timeout', value)

    def show_indexes(self, db, tbl):
        """
        Returns a dictionary of index for the database
        and table specified
        """
        cursor = self.cursor()
        sql = "SHOW INDEXES FROM %s" % self.quote_id(db, tbl)
        cursor.execute(sql)
        hdr = [d[0].lower() for d in cursor.description]
        info = {}
        for row in cursor.fetchall():
            row = dict(zip(hdr, row))
            info.setdefault(row.get('key_name'), [])\
                            .append(row.get('column_name'))
        cursor.close()
        return info

    def flush_logs(self):
        """
        Runs FLUSH LOGS
        """
        cursor = self.cursor()
        LOGGER.debug("Query: FLUSH LOGS executed.")
        cursor.execute('FLUSH LOGS')
        cursor.close()
    
    def flush_tables(self, table_list=None):
        """
        Runs FLUSH TABLES, by default flushes all tables.  Only flush specific
        tables by passing a list of database.table names.
        """
        if table_list:
            for db_and_table in table_list:
                db, table = db_and_table.split('.')
                cursor = self.cursor()
                LOGGER.debug('Query: FLUSH TABLES %s.%s' % (db, table))
                cursor.execute('FLUSH TABLES %s.%s' % (db, table))
        else:
            cursor = self.cursor()
            LOGGER.debug('Query: FLUSH TABLES')
            cursor.execute('FLUSH TABLES')
        cursor.close()
        
    def flush_tables_with_read_lock(self, extra_flush=False):
        """
        Runs FLUSH TABLES WITH READ LOCK
        """
        cursor = self.cursor()
        if extra_flush:
            LOGGER.debug('Query: FLUSH TABLES')   
            cursor.execute('FLUSH TABLES')
        LOGGER.debug('Query: FLUSH TABLES WITH READ LOCK')    
        cursor.execute('FLUSH TABLES WITH READ LOCK')
        cursor.close()

    def lock_tables(self, table_list=None):
        if not table_list:
            return
        query = 'LOCK TABLES ' + ' READ LOCAL, '.join(table_list)\
              + ' READ LOCAL'
        LOGGER.debug("Query: %s", query)
        cursor = self.cursor()
        cursor.execute(query)
        cursor.close()

    def unlock_tables(self):
        cursor = self.cursor()
        LOGGER.debug('Query: UNLOCK TABLES')
        cursor.execute('UNLOCK TABLES')
        cursor.close()
        
    def walk_databases(self):
        for db in self.show_databases():
            yield db

    def walk_tables(self, dbinclude=None):
        """
            walk_tables(self, include=None, exclude=None)
            Walks over the tables in the databases in include and returns
            (db, tbl_status) tuples where tbl_status is the dictionary from 
            a SHOW TABLE STATUS    row.
            if include is None, include all databases
                except those in exclude
            otherwise, only visit tables in the include list
                except those also in the exclude list
        """
        for db in self.show_databases():
            if db not in (dbinclude or ()):
                continue
            for tbl_status in self.show_table_status(db):
                tbl_status['db'] = db
                yield tbl_status

    def show_master_status(self):
        cursor = self.cursor()
        info = None
        if cursor.execute('SHOW MASTER STATUS'):
            info = cursor.fetchone()[0:2]
        cursor.close()
        return info

    def show_slave_status(self):
        cursor = self.cursor(MySQLdb.cursors.DictCursor)
        info = None
        cursor.execute('SHOW SLAVE STATUS')
        info = cursor.fetchone()
        cursor.close()
        return info

    def is_slave_running(self):
        info = self.show_slave_status()
        if not info:
            return False
        return (info.get('Slave_IO_Running', 'No') == 'Yes'
                and info.get('Slave_SQL_Running', 'No') == 'Yes')

    def start_slave(self):
        cursor = self.cursor()
        #FIXME: handle other warnings?
        LOGGER.debug("Query: START SLAVE")
        cursor.execute('START SLAVE')
        cursor.close()
    
    def stop_slave(self):
        if not self.is_slave_running():
            raise OperationalError("Slave is not running")
        cursor = self.cursor()
        cursor.execute('STOP SLAVE')
        messages = cursor.messages
        cursor.close()
        if messages:
            raise OperationalError("%s[%d]: %s" % messages[1])

    def show_transactional_engines(self):
        """
        show_transaction_engines(self)
        returns a list of engines with transactional capabilities suitable for
        mysqldump's --single-transaction flag
        """
        if self.server_version() < (5, 1, 2):
            # No access to an engines transactional status
            # before 5.1.2, so statically code the ones we
            # know about
            return ['innodb', 'berkelydb']
        else:
            cursor = self.cursor()
            cursor.execute("""SELECT Engine
                              FROM INFORMATION_SCHEMA.ENGINES
                              WHERE TRANSACTIONS = 'YES'""")
            result = [eng[0].lower() for eng in cursor.fetchall()]
            cursor.close()
            return result

    def server_version(self):
        """
        server_version(self)
        returns a numeric tuple: major, minor, revision versions (respectively)
        """
        version = self.get_server_info()
        m = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if m:
            return tuple(map(int, m.groups()))
        else:
            # TODO: make this prettier
            raise OperationalError("Could not match server version")

    def is_transactional(self, engine):
        if not engine:
            return False

        if not hasattr(self, '_txn_ngn_cache'):
            self._txn_ngn_cache = self.show_transactional_engines() + ['view']
        return engine.lower() in self._txn_ngn_cache

    def encode_as_filename(self, name):
        if self.server_version() < (5, 1, 2):
            raise OperationalError, \
                "MySQLClient.encode_as_filename not compatible with MySQL < 5.1."
                
        cursor = self.cursor()
        orig_charset = self.show_variable('character_set_results', 
                                           session_only=True)
        try:
            self.set_variable('character_set_results', 
                              'filename', 
                              session=True)
            cursor.execute('SELECT %s', name)
            filename, = [x for x, in cursor]
            cursor.close()
            self.set_variable('character_set_results', 
                              orig_charset, 
                              session=True)
        except OperationalError, e:
            # try again just to make sure
            self.set_variable('character_set_results', orig_charset, session=True)
            raise OperationalError, e
        return filename

    def show_encoded_dbs(self):
        if self.server_version() < (5, 1, 2):
            raise OperationalError, \
                "MySQLClient.show_encoded_dbs not compatible with MySQL < 5.1."
                
        charset_name = self.get_character_set_info()['name']
        self.set_character_set('binary')
        cursor = self.cursor()
        cursor.execute('''SELECT CONVERT(SCHEMA_NAME USING utf8) AS utf8_name,
                          CONVERT(SCHEMA_NAME USING filename) AS encoded_name
                          FROM INFORMATION_SCHEMA.SCHEMATA''')
        result = []
        for utf8_name, encoded_name in cursor:
            result.append((utf8_name, encoded_name))
        cursor.close()
        self.set_character_set(charset_name)
        return result

    def run_stmt(self, sql):
        cursor = self.cursor()
        cursor.execute(sql)
        cursor.close()

    # pass through to underlying connection object
    def __getattr__(self, key):
        return getattr(self._conn, key)

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

def connect(**kwargs):
    args = {}
    for key in kwargs:
        if key in CNF_TO_MYSQLDB:
            args[CNF_TO_MYSQLDB[key]] = kwargs[key]
        else:
            LOGGER.warn("Skipping unknown parameter %s", key)
    return MySQLClient(use_unicode=True, charset='utf8', **args)
