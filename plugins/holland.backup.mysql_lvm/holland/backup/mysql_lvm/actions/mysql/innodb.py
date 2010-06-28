"""Perform InnoDB recovery against a MySQL data directory"""

import os
import time
import signal
import logging
from cStringIO import StringIO
from subprocess import Popen, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from _mysqld import locate_mysqld_exe, generate_server_config, MySQLServer

LOG = logging.getLogger(__name__)

class InnodbRecoveryAction(object):
    def __init__(self, mysqld_config):
        self.mysqld_config = mysqld_config
        if 'datadir' not in mysqld_config:
            raise BackupError("datadir must be set for InnodbRecovery")

    def __call__(self, event, snapshot_fsm, snapshot):
        LOG.info("Starting InnoDB recovery")
        mycnf_path = os.path.join(self.mysqld_config['datadir'], 
                                  'my.innodb_recovery.cnf')
        self.mysqld_config['log-error'] = 'innodb_recovery.log'
        my_conf = generate_server_config(self.mysqld_config,
                                         mycnf_path)
        
        mysqld_exe = locate_mysqld_exe(self.mysqld_config)
        LOG.info("Bootstrapping with %s", mysqld_exe)
        mysqld = MySQLServer(mysqld_exe, my_conf)
        mysqld.start(bootstrap=True)

        while mysqld.poll() is None:
            if signal.SIGINT in snapshot_fsm.sigmgr.pending:
                mysqld.kill(signal.SIGKILL)
            time.sleep(0.5)
        LOG.info("%s has stopped", mysqld_exe)

        if mysqld.returncode != 0:
            datadir = self.mysqld_config['datadir']
            for line in open(os.path.join(datadir, 'innodb_recovery.log'), 'r'):
                LOG.error("%s", line.rstrip())
            raise BackupError("%s exited with non-zero status (%s) during "
                              "InnoDB recovery" % (mysqld_exe, mysqld.returncode))
        else:
            LOG.info("%s ran successfully", mysqld_exe)
