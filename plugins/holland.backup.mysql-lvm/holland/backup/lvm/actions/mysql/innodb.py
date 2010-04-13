"""InnoDB Recovery functionality"""

import os
import pwd
import grp
import errno
import tempfile
import shutil
import logging
import subprocess

LOGGER = logging.getLogger(__name__)

class InnoDBRecovery(object):
    """Start a bootstrap process on the target MySQL data directory and 
    allow InnoDB recovery to complete."""

    def __init__(self, mysqld=None):
        self.mysqld = mysqld

    # This should happen before we actually back anything up
    # normal backups should be at priority 50. We are at 10
    def run_recovery(self, datadir):
        """Run innodb recovery"""

        mysqld_path = self._find_mysqld()
        tmpdir = _make_mysql_tmpdir()
        status = _bootstrap_mysql(mysqld_path=mysqld_path,
                                  datadir=datadir,
                                  tmpdir=tmpdir)
        try:
            shutil.rmtree(tmpdir)
        except IOError, exc:
            LOGGER.error("Failed to cleanup innodb-recovery tmpdir %s: %s",
                         tmpdir,
                         exc)
        else:
            LOGGER.info("Cleaned up innodb-recovery tmpdir %s", tmpdir)
        return (status == 0)

    def _find_mysqld(self):
        """Find the mysqld process path"""
        if self.mysqld:
            if os.path.exists(self.mysqld):
                return self.mysqld
            else:
                raise OSError("%r does not exist")
        elif os.path.exists('/usr/libexec/mysqld'):
            return '/usr/libexec/mysqld'
        elif os.path.exists('/usr/sbin/mysqld'):
            return '/usr/sbin/mysqld'
        else:
            raise OSError("Could not find mysqld")
        
def _bootstrap_mysql(mysqld_path, datadir, tmpdir):
    """Run mysqld in --bootstrap mode to initiate InnoDB recovery"""
    argv = [
        mysqld_path,
        '--datadir=%s' % datadir,
        '--tmpdir=%s' % tmpdir,
        '--user=mysql',
        '--bootstrap',
        '--skip-slave-start',
        '--default-storage-engine=InnoDB'
    ]
    # This helps silence a MySQL error to clean up the error logs slightly
    relay_log = _find_relay_log(datadir)
    if relay_log:
        argv += ['--relay-log=%s' % relay_log]
    try:
        logging.info("Starting InnoDB Recovery")
        logging.info(' '.join(argv))
        pid = subprocess.Popen(argv,
                               # don't write anything to the bootstrap mysqld
                               stdin=open('/dev/null', 'r'),
                               # tie stdout, stderr together for logging
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               # don't leak our fds to mysqld
                               close_fds=True
                              )
    except OSError, exc:
        logging.error("Error when starting innodb recovery: %s", exc)
    
    logging.debug("mysqld.pid.stdout => %r", pid.stdout)
    interrupted = False
    while True:
        try:
            line = pid.stdout.readline().strip()
            if not line:
                break
            logging.info("mysql[%d]: %s", pid.pid, line)
        except KeyboardInterrupt:
            # We wait here - we can't unmount the snapshot until this is 
            # done anyway
            # I suppose we could kill -9 MySQL pid if we wanted to drop 
            # faster (maybe recovery is going very, very slow)
            logging.info("Interrupt received. "
                         "Waiting for InnoDB recovery to complete.")
            logging.debug("ignoring KeyboardInterrupt(%r) until "
                          "ibrecovery completes")
            interrupted = True
            continue
        except IOError, exc:
            if exc.errno == errno.EINTR:
                logging.debug("Got EINTR while reading InnoDB data")
                continue
            # this probably means eof and python's io system is being janky
            elif exc.errno == 0:
                logging.debug("Skipping errno=0 OSError")
                break
            else:
                raise

    status = pid.wait()
    if interrupted:
        logging.debug("re-raising interrupt after shutdown")
        raise KeyboardInterrupt()
    return status

def _find_relay_log(path):
    """Find the relay-log-info location"""

    relay_log_info_file = os.path.join(path, 'relay-log.info')
    if os.path.exists(relay_log_info_file):
        relay_log = open(relay_log_info_file, 'r').readline().rstrip()
        relay_log = os.path.normpath(relay_log)
        basename = os.path.splitext(relay_log)[0]
        return basename
    return None

def _make_mysql_tmpdir():
    """Create a temporary directory for the MySQL instance"""
    tmpdir = tempfile.mkdtemp()
    LOGGER.debug("Created tmpdir for mysqld bootstrap: %s", tmpdir)
    os.chmod(tmpdir, 0770)
    LOGGER.debug("chmod %s u+g=rwx o-a", tmpdir)
    # set the tmpdir to whatever the mysql user is
    mysql_uid = pwd.getpwnam('mysql').pw_uid
    mysql_gid = grp.getgrnam('mysql').gr_gid
    os.chown(tmpdir, mysql_uid, mysql_gid)
    LOGGER.debug("Set %s owner/group to %s(%d)/%s(%d)",
                  tmpdir, 'mysql', mysql_uid, 'mysql', mysql_gid)
    return tmpdir
