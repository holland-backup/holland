import logging
from holland.core.backup import BackupError
from holland.lib.mysql import MySQLError

LOG = logging.getLogger(__name__)

class RecordMySQLReplicationAction(object):
    def __init__(self, client, config):
        self.client = client
        self.config = config

    def __call__(self, event, snapshot_fsm, snapshot_vol):
        record_master_status(self.client, self.config)
        record_slave_status(self.client, self.config)

def record_master_status(client, config):
    try:
        LOG.debug("Executing SHOW MASTER STATUS")
        master_status = client.show_master_status()
        if master_status:
            binlog = master_status['file']
            position = master_status['position']
            config['master_log_file'] = binlog
            config['master_log_pos'] = position
            LOG.info("Recorded binlog = %s position = %s",
                    binlog, position)
        else:
            LOG.info("This MySQL server does not have binary logs enabled. "
                     "Nothing to record from SHOW MASTER STATUS.")
    except MySQLError as exc:
        raise BackupError("MySQL error while acquiring master replication "
                          "status [%d] %s" % exc.args)

def record_slave_status(client, config):
    try:
        LOG.debug("Executing SHOW SLAVE STATUS")
        slave_status = client.show_slave_status()
        if slave_status:
            binlog = slave_status['relay_master_log_file']
            position = slave_status['exec_master_log_pos']
            config['slave_master_log_file'] = binlog
            config['slave_master_log_pos'] = position
            LOG.info("Recorded slave replication status: "
                     "master_binlog = %s master_position = %s",
                    binlog, position)
        else:
            LOG.info("This MySQL server is not a slave. "
                     "Nothing to record from SHOW SLAVE STATUS")
    except MySQLError as exc:
        raise BackupError("MySQL error while acquiring slave replication "
                          "status [%d] %s" % exc.args)
