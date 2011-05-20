"""
holland.backup.script
~~~~~~~~~~~~~~~~~~~~~

Holland backups via abitrary shell scripts

"""
import sys
import logging
from string import Template
from subprocess import Popen, STDOUT, PIPE
from holland.backup.script.util import size_to_bytes, cmd_to_size
from holland.core import BackupPlugin, BackupError
from holland.core.util import directory_size

LOG = logging.getLogger(__name__)

class CalledProcessError(Exception):
    """Raised if an error is encountered while executing a script"""

class ScriptPlugin(BackupPlugin):

    def estimate(self):
        return 0

    def backup(self):
        config = self.config['script']
        cmd_tpl = Template(config['cmd'])
        cmd = cmd_tpl.safe_substitute(backupdir=self.backup_directory)

        LOG.info("+ %s", cmd)
        try:
            pid = Popen([
                        config['shell'],
                        '-c',
                        cmd
                    ],
                    stdin=open('/dev/null', 'r'),
                    stdout=PIPE,
                    stderr=STDOUT,
                    close_fds=True
                )
            paragraph = False
            line = pid.stdout.readline()
            while line != '':
                if not paragraph:
                    LOG.info(":: ")
                    paragraph = True
                LOG.info("+ %s", line.rstrip())
                line = pid.stdout.readline()
            pid.wait()
            if pid.returncode != 0:
                raise CalledProcessError("script with exited non-zero status")
        except OSError, exc:
            raise BackupError("%s failed: %s" % (cmd, exc))

    def dryrun(self):
        config = self.config['script']
        cmd_tpl = Template(config['cmd'])
        cmd = cmd_tpl.safe_substitute(backupdir=self.backup_directory)
        LOG.info("+ %s", cmd)

    def plugin_info(self):
        return dict(
            name='script',
            author='Holland Core Development Team',
            summary="Backup method using abitrary shell scripts",
            description='''
            A very simple backup plugin for holland that allows executing arbitrary scripts

            This replaces a single variable called ${backupdir} with the actual
            holland backup directory.

            A command is considered as failed if it exits with non-zero status.
            ''',
            version='1.0',
            api_version='1.1.0',
        )

    def configspec(self):
        spec = super(ScriptPlugin, self).configspec()
        return spec.merge(spec.from_string("""
        [script]
        shell = string(default="/bin/sh")
        cmd = string(default="/bin/true")
        """)
        )
