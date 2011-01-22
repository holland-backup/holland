try:
    from os import devnull
except ImportError:
    devnull = '/dev/null'
import logging
from subprocess import Popen, PIPE, STDOUT
from holland.core.backup.hooks import BackupHook
from holland.core.plugin import PluginInfo
from holland.core.config import Configspec
from string import Template

LOG = logging.getLogger(__name__)

class CommandHook(BackupHook):
    def execute(self, job):
        config = job.config['holland:hook:cmd']
        cmd = Template(config['cmd']).safe_substitute(backupdir=job.store.path)
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
        return Configspec("""
        [holland:hook:cmd]
        shell = string(default="/bin/sh")
        cmd = string(default="/bin/true")
        """.splitlines()
        )
    def plugin_info(self):
        return PluginInfo(
            author='Andrew Garner',
            name='cmdhook',
            summary='Run arbitrary commands at different stages in the backup lifecycle',
            description='''

            ''',
            version='1.0a1',
            api_version='1.1.0a1',
        )
