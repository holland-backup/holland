"""Perform InnoDB recovery against a MySQL data directory"""

import os
import time
import signal
import logging
from cStringIO import StringIO
from subprocess import Popen, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from holland.lib.which import which, WhichError

LOG = logging.getLogger(__name__)

class InnodbRecoveryAction(object):
    def __init__(self, mysqld_config):
        self.mysqld_config = mysqld_config
        if 'datadir' not in mysqld_config:
            raise BackupError("datadir must be set for InnodbRecovery")

    def __call__(self, event, snapshot_fsm, snapshot):
        LOG.info("Starting InnoDB recovery")
        my_conf = generate_server_config(self.mysqld_config,
                                         self.mysqld_config['datadir'])
        
        mysqld_exe = locate_mysqld_exe(self.mysqld_config)
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

def locate_mysqld_exe(config):
    mysqld_candidates = config.pop('mysqld-exe')
    for candidate in mysqld_candidates:
        if os.path.isabs(candidate):
            path = [os.path.dirname(candidate)]
            candidate = os.path.basename(candidate)
        else:
            path = None # use environ[PATH]
        try:
            LOG.info("Looking for %s on %s", candidate, path or os.environ['PATH'])
            return which(candidate, path)
        except WhichError:
            LOG.debug("mysqld path %s does not exist - skipping", candidate)
    raise BackupError("Failed to find mysqld binary")

class MySQLServer(object):
    def __init__(self, mysqld_exe, defaults_file):
        self.mysqld_exe = mysqld_exe
        self.defaults_file = defaults_file
        self.returncode = None
        self.process = None

    def start(self, bootstrap=False):
        args = [
            self.mysqld_exe,
            '--defaults-extra-file=%s' % self.defaults_file,
        ]
        if bootstrap:
            args += ['--bootstrap']
        self.returncode = None
        LOG.info("Starting %s", list2cmdline(args))
        self.process = Popen(args, 
                             preexec_fn=os.setsid,
                             stdin=open('/dev/null', 'r'),
                             stdout=open('/dev/null', 'w'),
                             stderr=STDOUT,
                             close_fds=True)
    def stop(self):
        LOG.info("Stopping %s", self.mysqld_exe)
        if self.process:
            #os.kill(self.process.pid, signal.SIGTERM)
            LOG.info("Waiting for MySQL to stop")
            self.process.wait()
            LOG.info("%s stopped with status %d", self.mysqld_exe, self.process.returncode)
            self.returncode = self.process.returncode
            self.process = None

    def poll(self):
        self.returncode = self.process.poll()
        return self.returncode

    def kill(self, signum):
        os.kill(self.process.pid, signum)

    def restart(self):
        self.stop()
        self.start()

def generate_server_config(config, datadir):
    conf_data = StringIO()
    valid_params = [
        'innodb-buffer-pool-size', 
        'key-buffer', 
        'tmpdir', 
        'user', 
        'datadir'
    ]
    print >>conf_data, "[mysqld]"
    for key, value in config.iteritems():
        if key.replace('_', '-') not in valid_params:
            LOG.warning("Ignoring mysqld config parameter %s", key)
            continue
        print >>conf_data, "%s = %s" % (key, value)
    print >>conf_data, "# not used for --bootstrap but here for completeness"
    print >>conf_data, "port = 3307"
    print >>conf_data, "socket = /tmp/innodb_recovery.sock"
    print >>conf_data, "pid-file = /tmp/innodb_recovery.pid"
    print >>conf_data, "loose-skip-ndbcluster"
    print >>conf_data, "skip-slave-start"
    print >>conf_data, "skip-log-bin"
    print >>conf_data, "skip-relay-log"
    print >>conf_data, "skip-relay-log-info-file"
    print >>conf_data, "log-error=%s/innodb_recovery.log" % datadir
    text = conf_data.getvalue()
    open(os.path.join(datadir, 'my.innodb_recovery.cnf'), 'w').write(text)
    return os.path.join(datadir, 'my.innodb_recovery.cnf')
