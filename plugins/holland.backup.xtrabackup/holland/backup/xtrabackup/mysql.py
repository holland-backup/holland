"""
holland.backup.xtrabackup.mysql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simple mysql client wrapper
"""
import MySQLdb

class MySQL(object):
    MySQLError = MySQLdb.MySQLError

    def __init__(self, *args, **kwargs):
        self._connection = MySQLdb.connect(*args, **kwargs)

    def execute(self, sql, *args):
        cursor = self.cursor()
        try:
            return cursor.execute(sql, args)
        finally:
            cursor.close()

    def scalar(self, sql, *args):
        cursor = self.cursor()
        try:
            if cursor.execute(sql, args):
                return cursor.fetchone()[0]
            else:
                return None
        finally:
            cursor.close()

    def first(self, sql, *args):
        cursor = self.cursor()
        try:
            cursor.execute(sql, args)
            return cursor.fetchone()
        finally:
            cursor.close()

    def cursor(self):
        return self._connection.cursor()

    def from_defaults(cls, defaults_file):
        return cls(read_default_file=defaults_file)
    from_defaults = classmethod(from_defaults)

    def var(self, var, scope='SESSION'):
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
        try:
            return self._connection.close()
        finally:
            self._connection = None
