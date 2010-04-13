import logging

class DBRewriter(object):
    def __init__(self, dbmap):
        self.dbmap = dbmap

    def __call__(self, name):
        return self.dbmap.get(name, name)


def create_rewriter(databases):
    logging.debug("create_rewrite(%r)", databases)
    dbmap = {}
    for name in databases:
        logging.info("name = %r", name)
        if '=' in name:
            olddb, newdb = name.split('=')
            dbmap[olddb] = newdb
        else:
            dbmap[name] = name

    return DBRewriter(dbmap)
