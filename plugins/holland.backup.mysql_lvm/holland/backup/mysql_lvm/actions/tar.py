import os
import time
import signal
import logging
from subprocess import list2cmdline, Popen, CalledProcessError

LOG = logging.getLogger(__name__)

class TarArchiveAction(object):
    def __init__(self, snap_datadir, archive_stream, config):
        self.snap_datadir = snap_datadir
        self.archive_stream = archive_stream
        self.config = config

    def __call__(self, event, snapshot_fsm, snapshot_vol):
        argv = [
            'tar',
            '--create',
            '--file', '-',
            '--verbose',
            '--totals',
            '--directory', self.snap_datadir,
            '.'
        ]

        for param in self.config['exclude']:
            argv.insert(-1, "--exclude")
            argv.insert(-1, os.path.join('.', param))

        LOG.info("Running: %s > %s", list2cmdline(argv), self.archive_stream.name)

        archive_log = os.path.dirname(self.archive_stream.name)
        archive_log = os.path.join(archive_log, 'archive.log')
        process = Popen(argv,
                        preexec_fn=os.setsid,
                        stdout=self.archive_stream, 
                        stderr=open(archive_log, 'w'),
                        close_fds=True)
        while process.poll() is None:
            if signal.SIGINT in snapshot_fsm.sigmgr.pending:
                os.kill(process.pid, signal.SIGKILL)
            time.sleep(0.5)

        self.archive_stream.close()

        if signal.SIGINT in snapshot_fsm.sigmgr.pending:
            raise KeyboardInterrupt("Interrupted")

        if process.returncode != 0:
            raise CalledProcessError(process.returncode, "tar")
