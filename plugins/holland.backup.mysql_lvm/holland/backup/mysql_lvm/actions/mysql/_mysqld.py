"""Common mysqld bootstrapping functionality"""

import logging
import os
from io import StringIO
from subprocess import STDOUT, Popen, list2cmdline

from holland.core.backup import BackupError
from holland.lib.which import which

LOG = logging.getLogger(__name__)


def locate_mysqld_exe(config):
    """find mysqld executable"""
    mysqld_candidates = config.pop("mysqld-exe")
    for candidate in mysqld_candidates:
        if os.path.isfile(candidate):
            return candidate
        try:
            return which(candidate)
        except BackupError:
            pass
    raise BackupError("Failed to find mysqld binary")


class MySQLServer(object):
    """Manage New MySQL Server"""

    def __init__(self, mysqld_exe, defaults_file):
        self.mysqld_exe = mysqld_exe
        self.defaults_file = defaults_file
        self.returncode = None
        self.process = None

    def start(self, bootstrap=False):
        """Start new database"""
        args = [self.mysqld_exe, "--defaults-file=%s" % self.defaults_file]
        if bootstrap:
            args += ["--bootstrap"]
        self.returncode = None
        LOG.info("Starting %s", list2cmdline(args))
        self.process = Popen(
            args,
            preexec_fn=os.setsid,
            stdin=open("/dev/null", "r"),
            stdout=open("/dev/null", "w"),
            stderr=STDOUT,
            close_fds=True,
        )

    def stop(self):
        """Stop new mysql server"""
        LOG.info("Stopping %s", self.mysqld_exe)
        if self.process:
            # os.kill(self.process.pid, signal.SIGTERM)
            LOG.info("Waiting for MySQL to stop")
            self.process.wait()
            LOG.info("%s stopped", self.mysqld_exe)
            self.returncode = self.process.returncode
            self.process = None

    def poll(self):
        """Check if database is running"""
        self.returncode = self.process.poll()
        return self.returncode

    def kill(self, signum):
        """Forcibly stop new database"""
        os.kill(self.process.pid, signum)

    def kill_safe(self, signum):
        """Try to stop new database"""
        try:
            self.kill(signum)
        except OSError:
            pass

    def restart(self):
        """Gracefully restart database"""
        self.stop()
        self.start()


def generate_server_config(config, path):
    """Build configuration for new database instance to use"""
    conf_data = StringIO()
    valid_params = [
        "innodb-buffer-pool-size",
        "innodb-log-file-size",
        "innodb-log-group-home-dir",
        "innodb-data-home-dir",
        "innodb-data-file-path",
        "innodb-fast-shutdown",
        "open-files-limit",
        "key-buffer-size",
        "tmpdir",
        "user",
        "datadir",
        "log-error",
        "socket",
        "pid-file",
        "port",
    ]
    print("[mysqld]", file=conf_data)
    for key, value in config.items():
        if key.replace("_", "-") not in valid_params:
            LOG.warning("Ignoring mysqld config parameter %s", key)
            continue
        print("%s = %s" % (key, value), file=conf_data)
    print("# not used for --bootstrap but here for completeness", file=conf_data)
    print("port = 3307", file=conf_data)
    print("loose-skip-ndbcluster", file=conf_data)
    print("skip-networking", file=conf_data)
    print("skip-slave-start", file=conf_data)
    print("skip-log-bin", file=conf_data)
    text = conf_data.getvalue()
    LOG.debug("Generating config: %s", text)
    open(path, "w").write(text)
    return path
