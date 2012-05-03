import re
from subprocess import Popen, PIPE, STDOUT, list2cmdline

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
