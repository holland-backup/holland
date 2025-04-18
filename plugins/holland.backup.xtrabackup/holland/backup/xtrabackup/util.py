# pylint: skip-file

"""
holland.backup.xtrabackup.util
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility methods used by the xtrabackup plugin
"""

import codecs
import logging
import re
import tempfile
from os.path import expanduser, isabs, join
from string import Template
from subprocess import PIPE, STDOUT, Popen, list2cmdline

from holland.core.backup import BackupError
from holland.lib.which import which

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
        fileobj = codecs.open(defaults_file, "a", encoding="utf8")
        try:
            for path in include:
                path = expanduser(path)
                LOG.info("  + Added !include %s", path)
                print("!include " + path, file=fileobj)

            if auth_opts:
                need_client_section = True
                for key in ("user", "password", "host", "port", "socket"):
                    value = auth_opts.get(key)
                    if value is None:
                        continue
                    if need_client_section:
                        LOG.info(
                            "  + Added [client] section with credentials \
                            from [mysql:client] section"
                        )
                        print("[client]", file=fileobj)
                        need_client_section = False
                    print("%s = %s" % (key, value), file=fileobj)
        finally:
            fileobj.close()
    except IOError as exc:
        raise BackupError("Failed to create %s: [%d] %s" % (defaults_file, exc.errno, exc.strerror))

    return defaults_file


def run_xtrabackup(args, stdout, stderr):
    """Run xtrabackup"""
    cmdline = list2cmdline(args)
    LOG.info("Executing: %s", cmdline)
    LOG.info("  > %s 2 > %s", stdout.name, stderr.name)
    try:
        process = Popen(args, stdout=stdout, stderr=stderr, close_fds=True)
    except OSError as exc:
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
        raise BackupError("innobackupex exited with failure status [%d]" % process.returncode)


def apply_xtrabackup_logfile(xb_cfg, backupdir, binary_xtrabackup=False):
    """Apply xtrabackup_logfile via innobackupex --apply-log [options] for version < 8.0
    With xtrabackup > 8.0 this should run xtrabackup --prepare --target-dir=backupdir/data
    """
    # run ${innobackupex} --apply-log ${backupdir}
    # only applies when streaming is not used
    stream_method = determine_stream_method(xb_cfg["stream"], binary_xtrabackup=binary_xtrabackup)
    if stream_method is not None:
        LOG.warning("Skipping --prepare/--apply-logs since backup is streamed")
        return

    if "--compress" in xb_cfg["additional-options"]:
        LOG.warning("Skipping --apply-logs since --compress option appears " "to have been used.")
        return

    if binary_xtrabackup:
        innobackupex = which("xtrabackup")
        args = [innobackupex, "--prepare", "--target-dir=" + join(backupdir, "data")]
    else:
        innobackupex = xb_cfg["innobackupex"]
        if not isabs(innobackupex):
            innobackupex = which(innobackupex)
        args = [innobackupex, "--apply-log", join(backupdir, "data")]

    cmdline = list2cmdline(args)
    LOG.info("Executing: %s", cmdline)
    try:
        process = Popen(args, stdout=PIPE, stderr=STDOUT, close_fds=True)
    except OSError as exc:
        raise BackupError("Failed to run %s: [%d] %s" % cmdline, exc.errno, exc.strerror)

    for line in process.stdout:
        LOG.info("%s", line.rstrip())
    process.wait()
    if process.returncode != 0:
        raise BackupError("%s returned failure status [%d]" % (cmdline, process.returncode))


def determine_stream_method(stream, binary_xtrabackup=False):
    """Calculate the stream option from the holland config"""
    stream = stream.lower()
    # For xtrabackup >= 8.0 settings of tar/tar4idb/yes/1/true are ignored and force the use of xbstream
    if stream in ("yes", "1", "true", "tar", "tar4ibd"):
        return "xbstream" if binary_xtrabackup else "tar"
    if stream in ("xbstream",):
        return "xbstream"
    if stream in ("no", "0", "false"):
        return None
    raise BackupError("Invalid xtrabackup stream method '%s'" % stream)


def evaluate_tmpdir(tmpdir=None, basedir=None):
    """Evaluate the tmpdir option"""
    if tmpdir is None:
        return basedir
    if not tmpdir:
        return tempfile.gettempdir()
    if basedir:
        return tmpdir.replace("{backup_directory}", basedir)
    return tmpdir


def execute_pre_command(pre_command, **kwargs):
    """Execute a pre-command"""
    if not pre_command:
        return

    pre_command = Template(pre_command).safe_substitute(**kwargs)
    LOG.info("Executing pre-command: %s", pre_command)
    try:
        process = Popen(pre_command, stdout=PIPE, stderr=STDOUT, shell=True, close_fds=True)
    except OSError as exc:
        # missing executable
        raise BackupError("pre-command %s failed: %s" % (pre_command, exc.strerror))

    for line in process.stdout:
        LOG.info("  >> %s", line)
    returncode = process.wait()
    if returncode != 0:
        raise BackupError("pre-command exited with failure status [%d]" % returncode)


def add_xtrabackup_defaults(defaults_path, **kwargs):
    """get defaults for xtrabackup"""
    if not kwargs:
        return
    fileobj = open(defaults_path, "a")
    try:
        try:
            # spurious newline for readability
            print(file=fileobj)
            print("[xtrabackup]", file=fileobj)
            for key, value in list(kwargs.items()):
                print("%s = %s" % (key, value), file=fileobj)
        except IOError:
            raise BackupError("Error writing xtrabackup defaults to %s" % defaults_path)
    finally:
        fileobj.close()


def build_xb_args(config, basedir, defaults_file=None, binary_xtrabackup=False):
    """Build the commandline for xtrabackup"""
    if binary_xtrabackup:
        innobackupex = which("xtrabackup")
    else:
        innobackupex = config["innobackupex"]
        if not isabs(innobackupex):
            innobackupex = which(innobackupex)

    ibbackup = config["ibbackup"]
    stream = determine_stream_method(config["stream"], binary_xtrabackup=binary_xtrabackup)
    tmpdir = evaluate_tmpdir(config["tmpdir"], basedir)
    slave_info = config["slave-info"]
    safe_slave_backup = config["safe-slave-backup"]
    no_lock = config["no-lock"]
    strict = config["strict"]
    # filter additional options to remove any empty values
    extra_opts = [_f for _f in config["additional-options"] if _f]

    args = [innobackupex]
    if defaults_file:
        args.append("--defaults-file=" + defaults_file)
    if ibbackup:
        args.append("--ibbackup=" + ibbackup)

    if not binary_xtrabackup:
        if stream:
            args.append("--stream=" + stream)
        else:
            basedir = join(basedir, "data")
        if tmpdir:
            args.append("--tmpdir=" + tmpdir)
    else:
        args.append("--backup")
        if stream:
            args.append("--stream=xbstream")
        else:
            args.append("--target-dir=%s" % join(basedir, "data"))

    if slave_info:
        args.append("--slave-info")
    if safe_slave_backup:
        args.append("--safe-slave-backup")
    if no_lock:
        args.append("--no-lock")

    if not strict:
        args.append("--strict=OFF")
    if int(xtrabackup_version().split(".")[0]) < 8:
        args.append("--no-timestamp")
    if extra_opts:
        args.extend(extra_opts)
    if not binary_xtrabackup:
        if basedir:
            args.append(basedir)
    return args


def xtrabackup_version():
    """Get xtrabackup version"""
    xtrabackup_binary = "xtrabackup"
    if not isabs(xtrabackup_binary):
        xtrabackup_binary = which(xtrabackup_binary)
    xb_version = [xtrabackup_binary, "--version"]
    cmdline = list2cmdline(xb_version)
    LOG.info("Executing: %s", cmdline)
    try:
        process = Popen(xb_version, stdout=PIPE, stderr=STDOUT, close_fds=True)
    except OSError as exc:
        raise BackupError("Failed to run %s: [%d] %s" % cmdline, exc.errno, exc.strerror)

    for line in process.stdout:
        if isinstance(line, bytes):
            line = line.rstrip().decode("UTF-8")
        if "version" in line:
            xtrabackup_version = re.search(r"version\s*([\d.]+)", line).group(1)
        LOG.info("# %s", line)

    process.wait()
    if process.returncode != 0:
        raise BackupError("%s returned failure status [%d]" % (cmdline, process.returncode))
    return xtrabackup_version
