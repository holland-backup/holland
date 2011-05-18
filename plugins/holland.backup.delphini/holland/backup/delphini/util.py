# coding: utf-8
"""
holland.backup.delphini.util
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions to run arbitrary commands either locally or via ssh as
running various ndb cluster commands

:copyright: 2010-2011 by Andrew Garner
:license: BSD, see LICENSE.rst for details
"""

import os
import re
import logging
from subprocess import Popen, PIPE, list2cmdline
from holland.backup.delphini.error import ClusterError, ClusterCommandError
from holland.backup.delphini.pycompat import namedtuple

LOG = logging.getLogger(__name__)

def run_command(args, stdout=PIPE, stderr=PIPE):
    """Run a command and returns its stdout, stderr and exit status

    If stdout or stderr is not set to PIPE, ``None`` will be returned
    for that value rather than the string output.

    stdout and stderr must be a valid file descriptor.

    :returns: stdout (str or None), stderr (str or None), status (int)
    """
    LOG.info(" + %s", list2cmdline(args))
    try:
        process = Popen(
            list(args),
            stdin=open("/dev/null", "r"),
            stdout=stdout,
            stderr=stderr,
            close_fds=True
        )
    except OSError, exc:
        raise ClusterError("Could not run %s: %s" %
                          (args[0], exc))

    stdout, stderr = process.communicate()

    if stderr is not None:
        for line in str(stderr).splitlines():
            LOG.info(" ! %s", line)

    if stdout is not None:
        for line in str(stdout).splitlines():
            LOG.info(" > %s", line)

    return  stdout, stderr, process.returncode

def rsync(host, keyfile, remote_path, local_path):
    """Rsync a remote directory to a local directory

    This method will always rsync over ssh

    :param host: hostname to rsync from
    :param keyfile: ssh private key to use for auth
    :param remote_path: remote path to rsync from
    :param local_path: local path to rsync to
    """
    args = [
        'rsync',
        '-avz',
        '-e', 'ssh -o BatchMode=yes',
        host + ':' + remote_path + '/',
        local_path
    ]
    if keyfile is not None:
        args[3] += ' -i ' + keyfile
    run_command(args)

def ssh(hostname, command, keyfile=None, ssh_bin='ssh', **kwargs):
    """SSH to the specified host and run a command

    :param hostname: host to connect to with ssh
    :param command: command string to run over ssh
    :param keyfile: keyfile to use for authenticating over ssh
    :param ssh: ssh command to use, if 'ssh' is not in PATH
    :param kwargs: additional keyword parameters to pass to run_command
                   this can be used to redirect stdout/stderr for ssh

    :raises: ClusterError if ssh could not be run
    :returns: stdout (str or None), stderr (str or None)
    """
    args = [
        ssh_bin,
        '-o', 'BatchMode=yes',
        hostname,
        command
    ]

    if keyfile is not None:
        args.insert(-2, '-i')
        args.insert(-2, keyfile)

    stdout, stderr, status = run_command(
        args,
        **kwargs
    )

    if status != 0:
        raise ClusterCommandError("%s exited with non-zero status %d" %
                                  (list2cmdline(args), status),
                                  status=status)

    return stdout, stderr

def query_ndb(dsn, query, query_type='ndbd', ndb_config='ndb_config'):
    """Query an ndb cluster and return a dict

    'hostname' will always be included in the query results and a dict
    of hostname -> query row will be returned.

    :param dsn: data source name for connecting to the cluster
    :param query: query attributes
    :param query_type: type of the ndb query (defaults to 'ndbd')
    :param ndb_config: ndb_config command to use

    :returns: dict of hostname -> namedtuple
    """
    query = ['hostname'] + list(query)
    stdout, _, status = run_command([
        ndb_config,
        '--connect-string=%s' % dsn,
        '--type=%s' % query_type,
        '--query=%s' % ','.join(query),
        '--fields=:',
        '--rows=\\n'
    ])

    query_ntuple = namedtuple('Query', ' '.join(query))
    if status != 0:
        raise ClusterCommandError("ndb_config exited with non-zero status %d" %
                                  status,
                                  status=status)

    nodes = {}
    for line in str(stdout).splitlines():
        row = line.split(':')
        hostname = row[0]
        nodes[hostname] = query_ntuple(*row)
    return nodes


def run_cluster_backup(dsn):
    """Run a MySQL Cluster backup and wait until it completes

    This method will raise ClusterCommandError if ndb_mgm exits
    with non-zero status.

    :param dsn: connect-string for ndb_mgm

    :returns: backup_id (int), stop_gcp (int)
    """
    args = [
        'ndb_mgm',
        '-c',
        dsn,
        '-e',
        'START BACKUP WAIT COMPLETED'
    ]
    stdout, _, status = run_command(args)

    if status != 0:
        raise ClusterCommandError("ndb_mgm -e 'START BACKUP' exited with "
                                  "status %d" % status,
                                  status=status)

    # In case we abort without exiting non-zero?
    check_for_abort(stdout)
    backup_id = parse_backup_id(stdout)
    stop_gcp = parse_stop_gcp(stdout)
    return backup_id, stop_gcp

def check_for_abort(stdout):
    """Check for an abort message in the output of START BACKUP

    :raises: ClusterError if an abort is detected
    """
    for line in stdout.splitlines():
        if 'abort' in line:
            raise ClusterError(line)

def parse_backup_id(stdout):
    """Parse the backup id from the output of a START BACKUP ndb management
    directive

    :returns: backup_id (int)
    """
    match = re.search(r'Backup (?P<backup_id>\d+)', stdout, re.M)
    if not match:
        raise ClusterError("No backup id found in output")
    return int(match.group('backup_id'))

def parse_stop_gcp(stdout):
    """Parse StopGCP from START BACKUP output"""
    match = re.search(r'StopGCP: (?P<stop_gcp>[0-9]+)', stdout, re.M)
    if not match:
        raise ClusterError("No StopGCP found in output")
    return int(match.group('stop_gcp'))
