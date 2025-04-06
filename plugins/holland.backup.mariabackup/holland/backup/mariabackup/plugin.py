"""
holland.mysql.mariabackup
~~~~~~~~~~~~~~~~~~~~~~~

Backup plugin implementation to provide support for MariaDB-backup.
"""

import logging
from os.path import join
from subprocess import PIPE, STDOUT, Popen, list2cmdline

from holland.backup.mariabackup import util
from holland.core.backup import BackupError
from holland.core.util.path import directory_size
from holland.lib.compression import COMPRESSION_CONFIG_STRING, open_stream
from holland.lib.mysql import connect
from holland.lib.mysql.client.base import MYSQL_CLIENT_CONFIG_STRING
from holland.lib.mysql.option import build_mysql_config

LOG = logging.getLogger(__name__)

CONFIGSPEC = (
    """
[mariabackup]
global-defaults     = string(default='/etc/my.cnf')
innobackupex        = string(default='mariabackup')
ibbackup            = string(default=None)
stream              = string(default=mbstream)
apply-logs          = boolean(default=yes)
slave-info          = boolean(default=no)
safe-slave-backup   = boolean(default=no)
no-lock             = boolean(default=no)
tmpdir              = string(default=None)
additional-options  = force_list(default=list())
pre-command         = string(default=None)
"""
    + MYSQL_CLIENT_CONFIG_STRING
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


class MariabackupPlugin:
    """control connection to mysql server"""

    mysql = None

    """path to the my.cnf generated by this plugin"""
    defaults_path = None

    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.config.validate_config(CONFIGSPEC)
        self.target_directory = target_directory
        self.dry_run = dry_run

        defaults_path = join(self.target_directory, "my.cnf")
        client_opts = self.config["mysql:client"]
        includes = client_opts["defaults-extra-file"] + [
            self.config["mariabackup"]["global-defaults"]
        ]
        util.generate_defaults_file(defaults_path, includes, client_opts)
        self.defaults_path = defaults_path

    def estimate_backup_size(self):
        """Return estimated backup size"""
        mysql_config = build_mysql_config(self.config["mysql:client"])
        client = connect(mysql_config["client"])
        try:
            datadir = client.show_variable("datadir")
            return directory_size(datadir)
        except OSError as exc:
            raise BackupError(
                "Failed to calculate directory size: [%d] %s" % (exc.errno, exc.strerror)
            )
        finally:
            client.close()

    def open_mb_logfile(self):
        """Open a file object to the log output for mariabackup"""
        path = join(self.target_directory, "mariabackup.log")
        try:
            return open(path, "a")
        except IOError as exc:
            raise BackupError("[%d] %s" % (exc.errno, exc.strerror))

    def open_mb_stdout(self):
        """Open the stdout output for a streaming mariabackup run"""
        config = self.config["mariabackup"]
        backup_directory = self.target_directory
        stream = util.determine_stream_method(config["stream"])
        if stream:
            archive_path = join(backup_directory, "backup.mb")
            try:
                return open_stream(archive_path, "w", **self.config["compression"])
            except OSError as exc:
                raise BackupError("Unable to create output file: %s" % exc)
        else:
            return open("/dev/null", "w")

    def dryrun(self):
        """Test backup without preformaning backup"""

        mb_cfg = self.config["mariabackup"]
        args = util.build_mb_args(mb_cfg, self.target_directory, self.defaults_path)
        LOG.info("* mariabackup command: %s", list2cmdline(args))
        bin_path = util.get_mariadb_backup_bin_path(mb_cfg)
        args = [bin_path, "--defaults-file=" + self.defaults_path, "--help"]
        cmdline = list2cmdline(args)
        LOG.info("* Verifying generated config '%s'", self.defaults_path)
        LOG.debug("* Verifying via command: %s", cmdline)
        try:
            process = Popen(args, stdout=PIPE, stderr=STDOUT, close_fds=True)
        except OSError:
            raise BackupError("Failed to find mariabackup binary")
        stdout = process.stdout.read()
        process.wait()
        # Note: mariabackup --help will exit with 1 usually
        # New versions are return zero
        if process.returncode > 1:
            LOG.error("! %s failed. Output follows below.", cmdline)
            for line in stdout.splitlines():
                LOG.error("! %s", line)
            raise BackupError("%s exited with failure status [%d]" % (cmdline, process.returncode))

    def backup(self):
        """Perform Backup"""
        mb_cfg = self.config["mariabackup"]
        util.mariabackup_version(mb_cfg)
        if self.dry_run:
            self.dryrun()
            return
        backup_directory = self.target_directory
        tmpdir = util.evaluate_tmpdir(mb_cfg["tmpdir"], backup_directory)
        # innobackupex --tmpdir does not affect mariabackup
        util.add_mariabackup_defaults(self.defaults_path, tmpdir=tmpdir)
        args = util.build_mb_args(mb_cfg, backup_directory, self.defaults_path)
        util.execute_pre_command(
            mb_cfg["pre-command"], backup_directory=backup_directory, backupdir=backup_directory
        )
        stderr = self.open_mb_logfile()
        try:
            stdout = self.open_mb_stdout()
            exc = None
            try:
                try:
                    util.run_mariabackup(args, stdout, stderr)
                except Exception as exc:
                    LOG.info("!! %s", exc)
                    for line in open(join(self.target_directory, "mariabackup.log"), "r"):
                        LOG.error("    ! %s", line.rstrip())
                    raise
            finally:
                try:
                    stdout.close()
                except IOError as ex:
                    LOG.error("Error when closing %s: %s", stdout.name, ex)
                    if exc is None:
                        raise
        finally:
            stderr.close()
        if mb_cfg["apply-logs"]:
            util.apply_mariabackup_logfile(mb_cfg, backup_directory)
