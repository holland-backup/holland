"""
Restore support for LVM backups
"""

import os
from subprocess import Popen, PIPE, STDOUT
import logging
from holland.core.command import Command, option
from holland.lib.compression import open_stream

class LVMRestore(Command):
    """${cmd_usage}

    ${cmd_option_list}
    """

    name = 'lvm-restore'

    aliases = [
        'lvr'
    ]

    options = [
    ]

    def __init__(self, backup):
        Command.__init__(self)
        self.backup = backup

    def run(self, cmd, opts, directory):
        # LVM backups are strictly tar backups through some (or no) compression
        config = self.backup.config
        if 'lvmbackup' not in config:
            logging.error("Backupset %s is not a mysqldump backup.", self.backup.name)
            return 1

        path = os.path.join(self.backup.path, 'backup.tar')
        try:
            stream = open_stream(path, 'r', config['compression']['method'])
        except IOError, exc:
            logging.error("Failed to open stream: %s", path)
            return 1

        logging.info("Extracting LVM backup %s to %s", stream.name, os.path.abspath(directory))
        try:
            untar(stream, directory)
        except IOError, exc:
            logging.error("Failed to untar %s: %s", stream.name, exc)
            return 1

        return 0

def untar(stream, directory):
    args = [
        'tar',
        '--extract',
        '--verbose',
        '--directory', directory
    ]
    pid = Popen(args, close_fds=True, stdin=stream, stdout=PIPE, stderr=STDOUT)
    for line in pid.stdout:
        logging.info("tar[%d]: %s", pid.pid, line.rstrip())
    if pid.wait() != 0:
        raise IOError("Failed to untar stream")
