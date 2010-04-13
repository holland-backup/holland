import fnmatch
import logging

class SchemaFilter(object):
    def __init__(self, databases=None,
                       excluded_databases=None,
                       tables=None,
                       excluded_tables=None):
        self.databases = databases or ['*']
        self.tables = tables or ['*']
        self.database_exclusions = excluded_databases or []
        self.table_exclusions = excluded_tables or []

    def is_filtered(self, database, table):
        if database:
            for db in self.databases:
                if fnmatch.fnmatch(database, db):
                   break
            else:
                # If we didn't match any patterns, exclude the database
                return True

            for db in self.database_exclusions:
                if fnmatch.fnmatch(database, db):
                    return True

        if table:
            if not '.' in table:
                table = (database or '*') + '.' + table
            for tbl in self.tables:
                if '.' not in tbl:
                    tbl = '*.' + tbl
                if fnmatch.fnmatch(table, tbl):
                    break
            else:
                return True
    
            for tbl in self.table_exclusions:
                if '.' not in tbl:
                    tbl = '*.' + tbl

                if fnmatch.fnmatch(table, tbl):
                    return True

        return False
