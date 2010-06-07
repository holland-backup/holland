import logging

LOG = logging.getLogger(__name__)

class FlushAndLockMySQLAction(object):
    def __init__(self, client, extra_flush=True):
        self.client = client
        self.extra_flush = extra_flush

    def __call__(self, event, snapshot_fsm, snapshot_vol):
        if event == 'pre-snapshot':
            if self.extra_flush:
                LOG.info("Executing FLUSH TABLES")
                self.client.flush_tables()
            LOG.info("Executing FLUSH TABLES WITH READ LOCK")
            self.client.flush_tables_with_read_lock()
        elif event == 'post-snapshot':
            LOG.info("Executing UNLOCK TABLES")
            self.client.unlock_tables()
