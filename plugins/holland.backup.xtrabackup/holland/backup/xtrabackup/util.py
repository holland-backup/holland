import re
import logging
from subprocess import Popen, PIPE, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from holland.core.util.template import Template

LOG = logging.getLogger(__name__)

def xtrabackup_version(binary):
    args = [
        binary,
        '--no-defaults',
        '--version'
    ]
    process = Popen(args, stdout=PIPE, stderr=STDOUT, close_fds=True)
    stdout, _ = process.communicate()
    '''xtrabackup version 1.6.6 for Percona Server 5.1.59 unknown-linux-gnu'''
    m = re.match('^xtrabackup version (?P<version>\d+\.\d+\.\d+) ', stdout)
    if not m:
        raise BackupError("Could not find xtrabackup version.  %s returned %s" %
                          (list2cmdline(args), stdout))
    version_string = m.group('version')
    version_tuple = tuple(map(int, version_string.split('.')))
    return version_tuple

def get_stream_method(method):
    """Translate the backupset stream option to a valid argument
    for innobackupex --stream
    """
    if method == 'no':
        return None
    elif method in ('yes', 'tar'):
        return 'tar'
    else:
        return 'xbstream'

def resolve_template(value, **kwargs):
    return Template(value).safe_substitute(**kwargs)

def run_pre_command(command):
    process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
    LOG.info("Running pre-command: %s", command)
    for line in process.stdout:
        LOG.info("  %s", line)
    process.wait()
    if process.returncode != 0:
        raise BackupError("Pre-command %s exited with non-zero status %d" %
                          (command, process.returncode))
    else:
        LOG.info("Pre-command exited successfully.")
