"""Copy datadir from snapshot without creating a tar file """

import logging
import os
import signal
import time
from subprocess import CalledProcessError, Popen, list2cmdline

LOG = logging.getLogger(__name__)


class DirArchiveAction(object):
    """Copy datadir"""

    def __init__(self, snap_datadir, backup_datadir, config):
        self.snap_datadir = snap_datadir
        self.backup_datadir = backup_datadir
        self.config = config

    def __call__(self, event, snapshot_fsm, snapshot_vol):
        argv = ["cp", "--archive", self.snap_datadir, "-t", self.backup_datadir]

        LOG.info("Running: %s ", list2cmdline(argv))
        archive_log = os.path.join(self.backup_datadir, "../archive.log")

        process = Popen(
            argv,
            preexec_fn=os.setsid,
            stdout=open(archive_log, "w"),
            stderr=open(archive_log, "w"),
            close_fds=True,
        )
        while process.poll() is None:
            if signal.SIGINT in snapshot_fsm.sigmgr.pending:
                os.kill(process.pid, signal.SIGKILL)
            time.sleep(0.5)

        if signal.SIGINT in snapshot_fsm.sigmgr.pending:
            raise KeyboardInterrupt("Interrupted")

        if process.returncode != 0:
            LOG.error("dir exited with non-zero status: %d", process.returncode)
            LOG.error("Tailing up to the last 10 lines of archive.log for " "troubleshooting:")
            for line in open(archive_log, "r").readlines()[-10:]:
                LOG.error(" ! %s", line.rstrip())
            raise CalledProcessError(process.returncode, "dir")
