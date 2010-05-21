import os
import sys
import logging
from holland.backup.lvm.util import MySQLHelper, MySQLError
from holland.backup.lvm.core import mysql_snapshot_lifecycle
from holland.lib.compression import open_stream
from holland.core.util.path import directory_size
from holland.core.exceptions import BackupError

LOGGER = logging.getLogger(__name__)

CONFIGSPEC = """\
[mysql-lvm]
# default: mysql lv + _snapshot
snapshot-name = string(default=None)

# default: minimum of 20% of mysql lv or mysql vg free size
snapshot-size = string(default=None)

# default: temporary directory
snapshot-mountpoint = string(default=None)

# default: no
innodb-recovery = boolean(default=no)

# default: flush tables with read lock by default
lock-tables = boolean(default=yes)

# default: do an extra (non-locking) flush tables before
#          run flush tables with read lock
extra-flush-tables = boolean(default=yes)


[compression]
method = option('none', 'gzip', 'pigz', 'bzip2', 'lzop', default='gzip')
level = integer(min=0, max=9, default=1)

[mysql:client]
# default: ~/.my.cnf
defaults-file = string(default='~/.my.cnf')

# default: current user
user = string(default=None)

# default: none
password = string(default=None)

# default: localhost
host = string(default=None)

# default: 3306
port = integer(default=None)

# default: none
socket = string(default=None)

""".splitlines()

def mysql_auth_options(config):
    """Extract out valid MySQL auth options"""
    valid_options = [
        'user',
        'password',
        'host',
        'port',
        'socket',
        'defaults-file'
    ]
    # map normal names to MySQLdb keywords
    rewrite_options = {
        'password' : 'passwd',
        'socket' : 'unix_socket',
        'defaults-file' : 'read_default_file'
    }
    items = [(rewrite_options.get(key,key), value)
                for key, value in config.items()
                    if value and key in valid_options]
    return dict(items)

def mysql_lvm_options(config):
    LOGGER.debug("mysql_lvm_options(%r)", config)
    return {
        'innodb_recovery' : config['mysql-lvm']['innodb-recovery'],
        'flush_tables' : config['mysql-lvm']['lock-tables'],
        'extra_flush_tables' : config['mysql-lvm']['extra-flush-tables'],
        'snapshot_name' : config['mysql-lvm']['snapshot-name'],
        'snapshot_size' : config['mysql-lvm']['snapshot-size'],
        'snapshot_mountpoint' : config['mysql-lvm']['snapshot-mountpoint'],
    }

def compression_options(config):
    return config['method'], config['level']

class LVMBackup(object):
    CONFIGSPEC = CONFIGSPEC
    def __init__(self, name, config, directory, dry_run=False):
        self.config = config
        self.config.validate_config(CONFIGSPEC)
        LOGGER.debug("Validated config: %r", self.config)
        self.name = name
        self.directory = directory
        self.dry_run = dry_run

    def estimate_backup_size(self):
        try:
            client = MySQLHelper(**mysql_auth_options(self.config['mysql:client']))
        except MySQLError, exc:
            raise BackupError("[%d] %s" % exc.args)
        datadir = client.variable('datadir')
        return directory_size(datadir)

    def backup(self):
        if self.dry_run:
            return self._dry_run()
        destination = os.path.join(self.directory, 'backup.tar')
        zopts = compression_options(self.config['compression'])
        destination = open_stream(destination, 'w', *zopts)
        LOGGER.info("Saving snapshot to %s (compression=%s)",
                    destination.name, zopts[0])
        myauth = mysql_auth_options(self.config['mysql:client'])
        mylvmcfg = mysql_lvm_options(self.config)

        if 'innodb-recovery' in mylvmcfg:
            mylvmcfg['innodb-recovery'] = os.path.join(self.directory, 
                                                       'innodb_recovery.log')

        tar_log = open(os.path.join(self.directory, 'archive.log'), 'w')
        LOGGER.debug("Instantiating a new LVM snapshot lifecycle")
        lifecycle = mysql_snapshot_lifecycle(destination,
                                             mysql_auth=myauth,
                                             log_file=tar_log,
                                             replication_info_callback=self._save_replication_info,
                                             **mylvmcfg
                                            )
        try:
            lifecycle.run()
        except EnvironmentError,exc:
            raise BackupError(str(exc))

    def _dry_run(self):
        from holland.backup.lvm.actions.archive.tar import TarBackup
        from holland.backup.lvm.pylvm import LogicalVolume
        LOGGER.info("LVM dry-run")
        try:
            client = MySQLHelper(**mysql_auth_options(self.config['mysql:client']))
        except MySQLError, exc:
            raise BackupError("[%d] %s" % exc.args)
        datadir = client.variable('datadir')
        LOGGER.info("Backing up %s via snapshot", datadir)
        lv = LogicalVolume.find_mounted(datadir)
        if not lv:
            raise BackupError("%s is not on a logical volume" % datadir)
        LOGGER.info("%s is on logical volume /dev/%s/%s",
                    datadir,
                    lv.vg_name,
                    lv.lv_name)
        LOGGER.info("[dry-run] Snapshotting %s/%s to %s/%s_snapshot",
                    lv.vg_name,
                    lv.lv_name,
                    lv.vg_name,
                    lv.lv_name)
        LOGGER.info("[dry-run] Archiving:")
        archive = TarBackup(open('/dev/null', 'w'))
        archive.backup(datadir)

    def _save_replication_info(self, client):
        replication_info = dict()
        try:
            master_status = client.show_master_status()
            if not master_status:
                LOGGER.warning("No binary logs to record.")
            else:
                replication_info['master_log_file'] = master_status['file']
                replication_info['master_log_pos'] = master_status['position']
                LOGGER.info("Recorded binlog info: master_log_file='%s', master_log_pos=%d",
                            master_status['file'], master_status['position'])
        except MySQLError, exc:
            LOGGER.error("Failed to record master log information: [%d] %s",
                          *exc.args)

        try:
            slave_status = client.show_slave_status()
            if not slave_status:
                LOGGER.warning("No slave status to record.")
            else:
                log_file = slave_status['relay_master_log_file']
                log_pos = slave_status['exec_master_log_pos']
                replication_info['slave_master_log_file'] = log_file
                replication_info['slave_master_log_pos'] = log_pos
                LOGGER.info("Recorded slave position w/r/t master: "
                            "slave_master_log_file='%s', "
                            "slave_master_log_pos=%d",
                            log_file, log_pos)
        except MySQLError, exc:
            LOGGER.error("Failed to record MySQL slave log data: [%d] %s", 
                          *exc.args)

        self.config['mysql:replication'] = replication_info

