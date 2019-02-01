# pylint: skip-file

"""
holland.backup.mariabackup.mysql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple mysql client wrapper
"""
import MySQLdb
from holland.core.backup import BackupError


class MySQL(object):
    """Control MySQL Conntions"""

    MySQLError = MySQLdb.MySQLError

    def __init__(self, *args, **kwargs):
        self._connection = MySQLdb.connect(*args, **kwargs)

    def execute(self, sql, *args):
        """Execute MySQL Command"""
        cursor = self.cursor()
        try:
            return cursor.execute(sql, args)
        finally:
            cursor.close()

    def scalar(self, sql, *args):
        """Execute MySQL Commnad and return one value """
        cursor = self.cursor()
        try:
            if cursor.execute(sql, args):
                return cursor.fetchone()[0]
            return None
        finally:
            cursor.close()

    def first(self, sql, *args):
        """Execute MySQL Commnad and return first line"""
        cursor = self.cursor()
        try:
            cursor.execute(sql, args)
            return cursor.fetchone()
        finally:
            cursor.close()

    def cursor(self):
        """Get cursor object"""
        return self._connection.cursor()

    @classmethod
    def from_defaults(cls, defaults_file):
        """Read in default config options(?)"""
        return cls(read_default_file=defaults_file)

    def var(self, var, scope="SESSION"):
        """Get MySQL variables"""
        scope = scope.upper()
        if scope not in ("SESSION", "GLOBAL"):
            raise BackupError("Invalid variable scope used")
        var = var.replace("%", "\\%").replace("_", "\\_")
        sql = "SHOW %s VARIABLES LIKE '%s'" % (scope, var)
        try:
            return self.first(sql)[1]
        except IndexError:
            return None

    def close(self):
        """Close connection"""
        try:
            return self._connection.close()
        finally:
            self._connection = None
