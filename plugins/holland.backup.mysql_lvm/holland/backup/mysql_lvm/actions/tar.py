import os
import time
import shlex
import signal
import logging
from subprocess import list2cmdline, Popen, CalledProcessError
from holland.core.exceptions import BackupError

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

        pre_args = self.config['pre-args']
        if pre_args:
            LOG.info("Adding tar pre-args: %s", pre_args)
            pre_args = [arg.decode('utf8')
                        for arg in shlex.split(pre_args.encode('utf8'))]
            for option in pre_args:
                argv.insert(-3, option)
        for param in self.config['exclude']:
            argv.insert(-1, "--exclude")
            argv.insert(-1, os.path.join('.', param))
        post_args = self.config['post-args']
        if post_args:
            LOG.info("Adding tar post-args: %s", post_args)
            post_args = [arg.decode('utf8')
                         for arg in shlex.split(post_args.encode('utf8'))]
            for option in post_args:
                argv.append(option)
        LOG.info("Running: %s > %s", list2cmdline(argv), self.archive_stream.name)

        archive_dirname = os.path.dirname(self.archive_stream.name)
        if pre_args or post_args:
            warning_readme = os.path.join(archive_dirname, "NONSTD_TAR.txt")
            warning_log = open('warning_readme', 'w')
            print >>warning_log, ("This tar file was generated with non-std "
                                  "args:")
            print >>warning_log, list2cmdline(argv)
        archive_log = os.path.join(archive_dirname, 'archive.log')
        process = Popen(argv,
                        preexec_fn=os.setsid,
                        stdout=self.archive_stream,
                        stderr=open(archive_log, 'w'),
                        close_fds=True)
        while process.poll() is None:
            if signal.SIGINT in snapshot_fsm.sigmgr.pending:
                os.kill(process.pid, signal.SIGKILL)
            time.sleep(0.5)

        try:
            self.archive_stream.close()
        except IOError, exc:
            LOG.error("tar output stream %s failed: %s",
                      self.archive_stream.name, exc)
            raise BackupError(str(exc))

        if signal.SIGINT in snapshot_fsm.sigmgr.pending:
            raise KeyboardInterrupt("Interrupted")

        if process.returncode != 0:
            LOG.error("tar exited with non-zero status: %d",
                      process.returncode)
            LOG.error("Tailing up to the last 10 lines of archive.log for "
                      "troubleshooting:")
            for line in open(archive_log, 'r').readlines()[-10:]:
                LOG.error(" ! %s", line.rstrip())
            raise CalledProcessError(process.returncode, "tar")
