"""Common mysqld bootstrapping functionality"""

import os
import signal
import logging
from cStringIO import StringIO
from subprocess import Popen, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from holland.lib.which import which, WhichError

LOG = logging.getLogger(__name__)

def locate_mysqld_exe(config):
    mysqld_candidates = config.pop('mysqld-exe')
    for candidate in mysqld_candidates:
        if os.path.isabs(candidate):
            path = [os.path.dirname(candidate)]
            candidate = os.path.basename(candidate)
        else:
            path = None # use environ[PATH]
        try:
            LOG.debug("Searching for %s on path %s",
                      candidate, path or os.environ['PATH'])
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
            '--defaults-file=%s' % self.defaults_file,
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
            LOG.info("%s stopped", self.mysqld_exe)
            self.returncode = self.process.returncode
            self.process = None

    def poll(self):
        self.returncode = self.process.poll()
        return self.returncode

    def kill(self, signum):
        os.kill(self.process.pid, signum)

    def kill_safe(self, signum):
        try:
            self.kill(signum)
        except OSError:
            pass

    def restart(self):
        self.stop()
        self.start()

def generate_server_config(config, path):
    conf_data = StringIO()
    valid_params = [
        'innodb-buffer-pool-size',
        'innodb-log-file-size',
        'innodb-log-group-home-dir',
        'innodb-data-home-dir',
        'innodb-data-file-path',
        'innodb-fast-shutdown',
        'open-files-limit',
        'key-buffer-size',
        'tmpdir',
        'user',
        'datadir',
        'log-error',
        'socket',
        'pid-file',
        'port',
    ]
    print >>conf_data, "[mysqld]"
    for key, value in config.iteritems():
        if key.replace('_', '-') not in valid_params:
            LOG.warning("Ignoring mysqld config parameter %s", key)
            continue
        print >>conf_data, "%s = %s" % (key, value)
    print >>conf_data, "# not used for --bootstrap but here for completeness"
    print >>conf_data, "port = 3307"
    print >>conf_data, "loose-skip-ndbcluster"
    print >>conf_data, "skip-networking"
    print >>conf_data, "skip-slave-start"
    print >>conf_data, "skip-log-bin"
    text = conf_data.getvalue()
    LOG.debug("Generating config: %s", text)
    open(path, 'w').write(text)
    return path
