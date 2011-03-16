"""Utility methods for mysql cluster backups"""

import os
import re
import logging
from subprocess import Popen, PIPE, list2cmdline
from delphini.pycompat import namedtuple

LOG = logging.getLogger(__name__)

class ClusterError(Exception):
    """Raised when an error is encountered while backing up a MySQL Cluster"""

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
        for line in stderr.splitlines():
            LOG.info(" ! %s", line)

    if stdout is not None:
        for line in stdout.splitlines():
            LOG.info(" > %s", line)

    return  stdout, stderr, process.returncode

def ssh(hostname, command, keyfile=None, ssh='ssh', **kwargs):
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
        ssh,
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
        raise ClusterError("%s exited with non-zero status %d" %
                          (list2cmdline(args), status))

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
    stdout, stderr, status = run_command([
        ndb_config,
        '--connect-string=%s' % dsn,
        '--type=%s' % query_type,
        '--query=%s' % ','.join(query),
        '--fields=:',
        '--rows=\\n'
    ])

    Query = namedtuple('Query', ' '.join(query))
    if status != 0:
        raise ClusterError("ndb_config exited with non-zero status %d" % status)

    nodes = {}
    for line in stdout.splitlines():
        row = line.split(':')
        hostname = row[0]
        nodes[hostname] = Query(*row)
    return nodes


def run_cluster_backup(dsn):
    stdout, stderr, status = run_command(['ndb_mgm', '-c', dsn, '-e', 'START BACKUP WAIT COMPLETED'])

    if status != 0:
        raise ClusterError("START BACKUP exited with non-zero status %d" % status)

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
    m = re.search(r'Backup (?P<backup_id>\d+)', stdout, re.M)
    if not m:
        raise ClusterError("No backup id found in output")
    return int(m.group('backup_id'))

def parse_stop_gcp(stdout):
    m = re.search(r'StopGCP: (?P<stop_gcp>[0-9]+)', stdout, re.M)
    if not m:
        raise ClusterError("No StopGCP found in output")
    return int(m.group('stop_gcp'))

def archive_data_nodes(dsn,
                       backup_id,
                       ssh_user,
                       keyfile,
                       open_file=open):
    """Archive the backups specified by ``backup_id`` on the data nodes

    :param dsn: connection string to use to query the data nodes involved
    :param backup_id: backup_id of of the backup to archive on each node
    :param ssh_user: ssh user to use when archiving data
    :param keyfile: ssh keyfile to use for authentication

    :raises: ClusterError on failure
    """
    nodes = query_ndb(dsn, query=['backupdatadir'])

    for node in nodes:
        query = nodes[node]
        host = '%s@%s' % (ssh_user, node)
        remote_path = os.path.join(query.backupdatadir,
                                   'BACKUP',
                                   'BACKUP-%d' % backup_id)
        stdout, stderr = ssh(host,
                             'ls -lah ' + list2cmdline([remote_path]),
                             keyfile=keyfile)

        # XXX: compression for tar command
        ssh(host,
            'tar -cf - -C %s .' % list2cmdline([remote_path]),
            keyfile=keyfile,
            stdout=open_file("backup_%s_%d.tar" % (node, backup_id), 'w')
        )
        LOG.info("Archived node %s with backup id %d", node, backup_id)

def purge_backup(dsn, backup_id, ssh_user, keyfile):
    """Purge backups for a particular backup-id"""
    nodes = query_ndb(dsn, query=['backupdatadir'])
    for node in nodes:
        query = nodes[node]
        host = '%s@%s' % (ssh_user, node)
        remote_path = os.path.join(query.backupdatadir,
                                   'BACKUP',
                                   'BACKUP-%d' % backup_id)
        ssh(host,
            'rm -fr %s' % list2cmdline([remote_path]),
            keyfile=keyfile)

def backup(dsn, ssh_user, ssh_keyfile, open_file):
    """Backup a MySQL cluster"""
    backup_id, stop_gcp = run_cluster_backup(dsn=dsn)
    archive_data_nodes(dsn=dsn,
                       backup_id=backup_id,
                       ssh_user=ssh_user,
                       keyfile=ssh_keyfile,
                       open_file=open_file)
    purge_backup(dsn, backup_id, ssh_user, ssh_keyfile)
    return backup_id, stop_gcp
