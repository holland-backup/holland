import logging

LOG = logging.getLogger(__name__)

class FlushAndLockMySQLAction(object):
    def __init__(self, client, extra_flush=True):
        self.client = client
        self.extra_flush = extra_flush

    def __call__(self, event, snapshot_fsm, snapshot_vol):
        if event == 'pre-snapshot':
            if self.extra_flush:
                LOG.debug("Executing FLUSH TABLES")
                self.client.flush_tables()
            LOG.debug("Executing FLUSH TABLES WITH READ LOCK")
            LOG.info("Acquiring read-lock and flushing tables")
            self.client.flush_tables_with_read_lock()
        elif event == 'post-snapshot':
            LOG.info("Releasing read-lock")
            self.client.unlock_tables()
