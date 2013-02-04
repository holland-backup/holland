"""
holland.backup.xtrabackup.util
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility methods used by the xtrabackup plugin
"""

import codecs
import tempfile
import logging
from string import Template
from os.path import join, isabs, expanduser
from subprocess import Popen, PIPE, STDOUT, list2cmdline
from holland.core.backup import BackupError
from holland.lib.which import which, WhichError

LOG = logging.getLogger(__name__)

def generate_defaults_file(defaults_file, include=(), auth_opts=None):
    """Generate a mysql options file

    :param defaults_file: path where options should be written
    :param include: ordered list of additional defaults files to include
    :param auth_opts: dictionary of client options.  may include:
                      user, password, host, port, socket
    """
    LOG.info("* Generating mysql option file: %s", defaults_file)
    try:
        fileobj = codecs.open(defaults_file, 'a', encoding='utf8')
        try:
            for path in include:
                path = expanduser(path)
                LOG.info("  + Added !include %s", path)
                print >>fileobj, '!include ' + path

            if auth_opts:
                need_client_section = True
                for key in ('user', 'password', 'host', 'port', 'socket'):
                    value = auth_opts.get(key)
                    if value is None:
                        continue
                    if need_client_section:
                        LOG.info("  + Added [client] section with credentials from [mysql:client] section")
                        print >>fileobj, "[client]"
                        need_client_section = False
                    print >>fileobj, '%s = %s' % (key, value)
        finally:
            fileobj.close()
    except IOError, exc:
        raise BackupError("Failed to create %s: [%d] %s" %
                          (defaults_file, exc.errno, exc.strerror))

    return defaults_file

def run_xtrabackup(args, stdout, stderr):
    """Run xtrabackup"""
    cmdline = list2cmdline(args)
    LOG.info("Executing: %s", cmdline)
    LOG.info("  > %s 2 > %s", stdout.name, stderr.name)
    try:
        process = Popen(args, stdout=stdout, stderr=stderr, close_fds=True)
    except OSError, exc:
        # Failed to find innobackupex executable
        raise BackupError("%s failed: %s" % (args[0], exc.strerror))

    try:
        process.wait()
    except KeyboardInterrupt:
        raise BackupError("Interrupted")
    except SystemExit:
        raise BackupError("Terminated")

    if process.returncode != 0:
        # innobackupex exited with non-zero status
        raise BackupError("innobackupex exited with failure status [%d]" %
                          process.returncode)

def apply_xtrabackup_logfile(xb_cfg, backupdir):
    """Apply xtrabackup_logfile via innobackupex --apply-log [options]"""
    # run ${innobackupex} --apply-log ${backupdir}
    # only applies when streaming is not used
    stream_method = determine_stream_method(xb_cfg['stream'])
    if stream_method is not None:
        LOG.warning("Skipping --prepare/--apply-logs since backup is streamed")
        return

    if '--compress' in xb_cfg['additional-options']:
        LOG.warning("Skipping --apply-logs since --compress option appears "
                    "to have been used.")
        return

    innobackupex = xb_cfg['innobackupex']
    if not isabs(innobackupex):
        try:
            innobackupex = which(innobackupex)
        except WhichError:
            raise BackupError("Failed to find innobackupex script")
    args = [
        innobackupex,
        '--apply-log',
        backupdir
    ]

    cmdline = list2cmdline(args)
    LOG.info("Executing: %s", cmdline)
    try:
        process = Popen(args, stdout=PIPE, stderr=STDOUT, close_fds=True)
    except OSError, exc:
        raise BackupError("Failed to run %s: [%d] %s",
                          cmdline, exc.errno, exc.strerror)

    for line in process.stdout:
        LOG.info("%s", line.rstrip())
    process.wait()
    if process.returncode != 0:
        raise BackupError("%s returned failure status [%d]" %
                          (cmdline, process.returncode))

def determine_stream_method(stream):
    """Calculate the stream option from the holland config"""
    stream = stream.lower()
    if stream in ('yes', '1', 'true', 'tar', 'tar4ibd'):
        return 'tar'
    if stream in ('xbstream',):
        return 'xbstream'
    if stream in ('no', '0', 'false'):
        return None
    raise BackupError("Invalid xtrabackup stream method '%s'" % stream)

def evaluate_tmpdir(tmpdir=None, basedir=None):
    """Evaluate the tmpdir option"""
    if tmpdir is None:
        return basedir
    if not tmpdir:
        return tempfile.gettempdir()
    if basedir:
        return tmpdir.replace('{backup_directory}', basedir)
    return tmpdir


def execute_pre_command(pre_command, **kwargs):
    """Execute a pre-command"""
    if not pre_command:
        return

    pre_command = Template(pre_command).safe_substitute(**kwargs)
    LOG.info("Executing pre-command: %s", pre_command)
    try:
        process = Popen(pre_command,
                        stdout=PIPE,
                        stderr=STDOUT,
                        shell=True,
                        close_fds=True)
    except OSError, exc:
        # missing executable
        raise BackupError("pre-command %s failed: %s" %
                          (pre_command, exc.strerror))

    for line in process.stdout:
        LOG.info("  >> %s", process.pid, line)
    returncode = process.wait()
    if returncode != 0:
        raise BackupError("pre-command exited with failure status [%d]" %
                          returncode)

def add_xtrabackup_defaults(defaults_path, **kwargs):
    if not kwargs:
        return
    fileobj = open(defaults_path, 'a')
    try:
        try:
            # spurious newline for readability
            print >>fileobj
            print >>fileobj, "[xtrabackup]"
            for key, value in kwargs.iteritems():
                print >>fileobj, "%s = %s" % (key, value)
        except IOError, exc:
            raise BackupError("Error writing xtrabackup defaults to %s" %
                              defaults_path)
    finally:
        fileobj.close()
def build_xb_args(config, basedir, defaults_file=None):
    """Build the commandline for xtrabackup"""
    innobackupex = config['innobackupex']
    if not isabs(innobackupex):
        try:
            innobackupex = which(innobackupex)
        except WhichError:
            raise BackupError("Failed to find innobackupex script")

    ibbackup = config['ibbackup']
    stream = determine_stream_method(config['stream'])
    tmpdir = evaluate_tmpdir(config['tmpdir'], basedir)
    slave_info = config['slave-info']
    safe_slave_backup = config['safe-slave-backup']
    no_lock = config['no-lock']
    # filter additional options to remove any empty values
    extra_opts = filter(None, config['additional-options'])

    args = [
        innobackupex,
    ]
    if defaults_file:
        args.append('--defaults-file=' + defaults_file)
    if ibbackup:
        args.append('--ibbackup=' + ibbackup)
    if stream:
        args.append('--stream=' + stream)
    else:
        basedir = join(basedir, 'data')
    if tmpdir:
        args.append('--tmpdir=' + tmpdir)
    if slave_info:
        args.append('--slave-info')
    if safe_slave_backup:
        args.append('--safe-slave-backup')
    if no_lock:
        args.append('--no-lock')
    args.append('--no-timestamp')
    if extra_opts:
        args.extend(extra_opts)
    if basedir:
        args.append(basedir)
    return args
