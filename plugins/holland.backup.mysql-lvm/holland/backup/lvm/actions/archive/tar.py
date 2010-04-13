"""Tar archive implementation"""

import os
import sys
import errno
import subprocess
import signal
import logging

LOGGER = logging.getLogger(__name__)

class TarBackup(object):
    """Tar a directory write tar stream to  fileobject
    specified by 'dst'.

    If dst is a console, an OSError will be raised.
    dst must be a fileobject with a usable fileno() method"""

    def __init__(self, dst=sys.stdout):
        self.dst = dst
           
    def backup(self, directory):
        """Backup specified directory to dst file descriptor"""
        LOGGER.debug("TarBackup:backup(%r)", directory)
        if self.dst == sys.stdout:
            LOGGER.info("Streaming %r to stdout", self.dst)

        if hasattr(self.dst, 'isatty') and self.dst.isatty():
            LOGGER.error("Refusing to stream backup to console. "
                         "Please redirect stdout.")
            raise ValueError("destination is a console")

        argv = [
            'tar',
            '--create',
            '--file', '-',
            '--verbose',
            '--totals',
            '--directory', directory,
            '.'
        ]

        LOGGER.debug("Running %s", subprocess.list2cmdline(argv))
        tar_pid = subprocess.Popen(argv,
                               stdin=open('/dev/null', 'r'),
                               stdout=os.dup(self.dst.fileno()),
                               stderr=subprocess.PIPE,
                               close_fds=True)

        interrupted = False
        while True:
            try:
                line = tar_pid.stderr.readline().rstrip()
                if not line:
                    break
                LOGGER.info("tar[%d]: %s", tar_pid.pid, line.encode('utf8'))
            except KeyboardInterrupt:
                interrupted = True
                LOGGER.info("interrupted in the middle of archiving. "
                            "Sending SIGTERM to tar[%d]", tar_pid.pid)
                try:
                    os.kill(tar_pid.pid, signal.SIGTERM)
                except OSError, exc:
                    if exc.errno == errno.ESRCH:
                        LOGGER.info("tar has already stopped")
                    else:
                        raise
            except OSError, exc:
                if exc.errno == errno.EINTR:
                    continue
                raise

        status = tar_pid.wait()

        if status != 0:
            raise IOError("tar exited with non-zero status [%d]" % status)

        LOGGER.debug("tar exited with status = %d", status)
        if interrupted:
            LOGGER.debug("re-raising keyboard-interrupt")
            raise KeyboardInterrupt()

