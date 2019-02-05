"""
Find schema names that adhere to particular patterns
"""
import fnmatch
import string
import logging

LOG = logging.getLogger(__name__)


class MySQLFind(object):
    """
    Create list of included and excluded tables
    """

    def __init__(self, client, **kwargs):
        self.client = client
        self.dbinclude = list(kwargs.get("dbinclude") or ["*"])
        self.dbexclude = list(kwargs.get("dbexclude") or [])
        self.dbexclude.extend(["information_schema", "lost+found"])
        self.tblinclude = []
        self.filtered = False
        for pat in list(kwargs.get("tblinclude") or []):
            if "." not in pat:
                pat = "*." + pat
            self.tblinclude.append(pat)
        self.tblexclude = []
        for pat in list(kwargs.get("tblexclude") or []):
            if "." not in pat:
                pat = "*." + pat
            self.tblexclude.append(pat)

    @staticmethod
    def is_filtered(name, include_patterns, exclude_patterns):
        """
        Check if a string is filtered
        """
        # if a db.tbl name does not match an include pattern - filter it
        for pat in map(string.ascii_lowercase, include_patterns or ["*"]):
            if fnmatch.fnmatch(name.lower(), pat):
                break
        else:
            return True

        for pat in map(string.ascii_lowercase, exclude_patterns or []):
            if fnmatch.fnmatch(name.lower(), pat):
                return True
        return False

    def find_databases(self):
        """
        Find databases that match the given patterns
        """
        self.filtered = False
        result = []
        for name in self.client.show_databases():
            if not self.is_filtered(name, self.dbinclude, self.dbexclude):
                result.append(name)
            elif name not in ["information_schema", "lost+found"]:
                self.filtered = True
        return result

    def find_table_status(self):
        """
        Find table status
        """
        self.filtered = False
        for status in self.client.walk_tables(dbinclude=self.find_databases()):
            database = status["db"]
            if self.is_filtered(database, self.dbinclude, self.dbexclude):
                continue
            tbl = database + "." + status["name"]
            if self.is_filtered(tbl, self.tblinclude, self.tblexclude):
                continue
            yield status

    def find_tables(self):
        """
        Find tables that match the given patterns
        """
        self.filtered = False
        result = []
        for database in self.find_databases():
            for tbl in self.client.show_tables(database):
                name = database + "." + tbl
                if not self.is_filtered(name, self.tblinclude, self.tblexclude):
                    result.append(name)
                else:
                    self.filtered = True
        return result

    def find_non_transactional(self):
        """
        Check if table is transactional
        """
        for tbl_status in self.find_table_status():
            engine = tbl_status["engine"] or tbl_status["comment"]

            if self.client.is_transactional(engine):
                continue
            yield tbl_status["db"] + "." + tbl_status["name"], engine

    def find_excluded_tables(self):
        """
        Find tables that would be filtered by the
        given patterns
        """
        result = []
        for database in self.find_databases():
            for tbl in self.client.show_tables(database):
                name = database + "." + tbl
                if self.is_filtered(name, self.tblinclude, self.tblexclude):
                    result.append(name)
        return result

    def __repr__(self):
        return """DB Include: %s
        DB Exclude: %s
        TbL Include: %s
        Tbl Exclude: %s
        """ % (
            self.dbinclude,
            self.dbexclude,
            self.tblinclude,
            self.tblexclude,
        )
