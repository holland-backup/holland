try:
    from os import devnull
except ImportError:
    devnull = '/dev/null'
import logging
from subprocess import Popen, PIPE, STDOUT
from holland.core.backup.hooks import BackupHook
from holland.core.config import Configspec
from string import Template

LOG = logging.getLogger(__name__)

class CommandHook(BackupHook):
    def configure(self, config):
        self.config = self.configspec().validate(config)

    def register(self, signal_group):
        event = self.config['events']
        LOG.info("Connecting to signal %s [%r]",
                 event, signal_group[event])
        signal_group[event].connect(self, weak=False)

    def execute(self, job):
        config = self.config
        cmd = Template(config['cmd']).safe_substitute(backupdir=job.store.path,
                                                      plugin=job.plugin.plugin_info()['name'],
                                                      backupset=job.store.name
                                                      )
        args = [
            config['shell'], '-c',
            cmd
        ]
        pid = Popen(args,
                    stdin=open(devnull, 'w'),
                    stdout=PIPE,
                    stderr=STDOUT,
                    close_fds=True)
        LOG.info("+ [%d] %s::", pid.pid, cmd)
        LOG.info("")
        for line in pid.stdout:
            LOG.info("+ %s", line.rstrip())
        pid.wait()
        if pid.returncode != 0:
            LOG.warning("+ [command-hook] Warning exited non-zero status %d",
                        pid.returncode)

    def configspec(self):
        return Configspec.from_string("""
        events = option('before-backup', 'after-backup', default='after-backup')
        shell = string(default="/bin/sh")
        cmd = string(default="/bin/true")
        """)

    def plugin_info(self):
        return dict(
            author='Andrew Garner',
            name='cmdhook',
            summary='Run arbitrary commands at different stages in the backup lifecycle',
            description='''

            ''',
            version='1.0a1',
            api_version='1.1.0a1',
        )
