"""MySQL Manager callback"""

import logging

LOGGER = logging.getLogger(__name__)

class MySQLManager(object):
    """Manage MySQL lock behavior"""
    def __init__(self,
                 mysqlhelper,
                 flush_tables=True,
                 extra_flush_tables=True):
        self.mysqlhelper = mysqlhelper
        self.flush_tables = flush_tables
        self.extra_flush_tables = extra_flush_tables

    def lock(self):
        """Flush and lock tables in the target MySQL instance"""
        if self.flush_tables and self.extra_flush_tables:
            LOGGER.info("FLUSH TABLES")
            self.mysqlhelper.flush_tables()
        else:
            LOGGER.warning("Extra flush tables disabled.")

        if self.flush_tables:
            LOGGER.info("FLUSH TABLES WITH READ LOCK")
            self.mysqlhelper.flush_tables_with_read_lock()
        else:
            LOGGER.warning("Flush tables has been disabled. "
                           "No read lock acquired.")

    def unlock(self):
        """Unlock tables in the target MySQL instance"""
        # only unlock if we locked to begin with
        if self.flush_tables:
            LOGGER.info("UNLOCK TABLES")
            self.mysqlhelper.unlock_tables()
