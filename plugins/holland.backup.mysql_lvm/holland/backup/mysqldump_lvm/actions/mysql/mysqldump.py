"""Dispatch to the holland mysqldump plugin"""

import os
import time
import signal
import logging
from cStringIO import StringIO
from subprocess import Popen, STDOUT, list2cmdline
from holland.core.exceptions import BackupError

LOG = logging.getLogger(__name__)

class MySQLDumpDispatchAction(object):
    def __init__(self, mysqldump_plugin, datadir):
        self.mysqldump_plugin = mysqldump_plugin
        self.datadir = datadir

    def __call__(self, event, snapshot_fsm, snapshot):
        LOG.info("MySQLDumpDispatch")
        my_conf = generate_server_config(self.datadir)
        mysqld = MySQLServer('/usr/libexec/mysqld', my_conf)
        mysqld.start(bootstrap=False)
        time.sleep(5)
        self.mysqldump_plugin.config['mysql:client']['socket'] = os.path.join(self.datadir, 'holland_mysqldump.sock')
        self.mysqldump_plugin.mysql_config['client']['socket'] = os.path.join(self.datadir, 'holland_mysqldump.sock')
        self.mysqldump_plugin.config['mysqldump']['bin-log-position'] = False # we don't suport this directly
        self.mysqldump_plugin.backup()
        mysqld.kill(signal.SIGKILL) # DIE DIE DIE
        mysqld.stop() # we dont' really care about the exit code, if mysqldump ran smoothly :)

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
                             #stdout=open('/dev/null', 'w'),
                             #stderr=STDOUT,
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

def generate_server_config(datadir):
    conf_data = StringIO()
    print >>conf_data, "[mysqld]"
    print >>conf_data, "user=mysql"
    print >>conf_data, "datadir = %s" % datadir
    print >>conf_data, "innodb-buffer-pool-size = 32M"
    print >>conf_data, "key-buffer-size = 32M"
    print >>conf_data, "# not used for --bootstrap but here for completeness"
    print >>conf_data, "port = 3307"
    print >>conf_data, "socket = %s" % os.path.join(datadir, 'holland_mysqldump.sock')
    print >>conf_data, "pid-file = %s/innodb_recovery.pid" % datadir
    print >>conf_data, "loose-skip-ndbcluster"
    print >>conf_data, "skip-slave-start"
    print >>conf_data, "skip-log-bin"
    print >>conf_data, "skip-relay-log"
    print >>conf_data, "skip-relay-log-info-file"
    print >>conf_data, "log-error=%s/innodb_recovery.log" % datadir
    text = conf_data.getvalue()
    open(os.path.join(datadir, 'my.mysqldump.cnf'), 'w').write(text)
    return os.path.join(datadir, 'my.mysqldump.cnf')
