"""
holland.backup.xtrabackup.mysql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple mysql client wrapper
"""
import MySQLdb
from holland.core.backup import BackupError

class MySQL(object):
    """Class for connecting to MySQl"""
    MySQLError = MySQLdb.MySQLError

    def __init__(self, *args, **kwargs):
        self._connection = MySQLdb.connect(*args, **kwargs)

    def execute(self, sql, *args):
        """execute SQL command"""
        cursor = self.cursor()
        try:
            return cursor.execute(sql, args)
        finally:
            cursor.close()

    def scalar(self, sql, *args):
        """return single object"""
        cursor = self.cursor()
        try:
            if cursor.execute(sql, args):
                return cursor.fetchone()[0]
            return None
        finally:
            cursor.close()

    def first(self, sql, *args):
        """return first tuple"""
        cursor = self.cursor()
        try:
            cursor.execute(sql, args)
            return cursor.fetchone()
        finally:
            cursor.close()

    def cursor(self):
        """return cursor object"""
        return self._connection.cursor()


    @classmethod
    def from_defaults(cls, defaults_file):
        """return defaults"""
        return cls(read_default_file=defaults_file)

    def var(self, var, scope='SESSION'):
        """return database variables"""
        scope = scope.upper()
        if scope not in ('SESSION', 'GLOBAL'):
            raise BackupError("Invalid variable scope used")
        var = var.replace('%', '\\%').replace('_', '\\_')
        sql = "SHOW %s VARIABLES LIKE '%s'" % (scope, var)
        try:
            return self.first(sql)[1]
        except IndexError:
            return None

    def close(self):
        """close connection"""
        try:
            return self._connection.close()
        finally:
            self._connection = None
