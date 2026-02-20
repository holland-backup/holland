"""mariadb-dump support"""

import errno
import logging
import os
import re
import subprocess
from tempfile import TemporaryFile

LOG = logging.getLogger(__name__)

ALL_DATABASES = object()

OPTION_ARG_CRE = re.compile(r"^(--[^=]+)(?:=(.+))?$", re.UNICODE)

CHECK_VERSION_OPTIONS = {
    "--order-by-size": (10, 9, 1),
    "--dump-history": (10, 11, 0),
}

CHECK_OPTION_ARG_PATTERNS = {
    "--max-allowed-packet": r"\w",
    "--default-character-set": r"\w",
    "--master-data": r"^[12]$",
}


class MariaDBDumpError(Exception):
    """Excepton class for MariaDump errors"""


class MariaDBDumpOptionError(Exception):
    """Exception class for MariaDB Option validation"""


class MariaDBDump:
    """mariadb-dump command runner"""

    @classmethod
    def get_version(cls, command):
        """Return the version of the given mariadb-dump command"""
        args = [command, "--no-defaults", "--version"]
        list2cmdline = subprocess.list2cmdline
        cmdline = list2cmdline(args)
        LOG.debug("Executing: %s", cmdline)
        try:
            process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True
            )
            stdout, _ = process.communicate()
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                raise MariaDBDumpError("'%s' does not exist" % command)
            raise MariaDBDumpError(
                "Error[%d:%s] when trying to run '%s'"
                % (exc.errno, errno.errorcode[exc.errno], command)
            )

        if process.returncode != 0:
            LOG.error("%s exited with non-zero status[%d]", cmdline, process.returncode)
            for line in stdout.splitlines():
                LOG.error("! %s", line)
        try:
            return tuple(
                (
                    int(digit)
                    for digit in re.search(
                        r"(\d+)[.](\d+)[.](\d+)", stdout.decode("utf-8")
                    ).groups()
                )
            )
        except AttributeError:
            LOG.debug("%s provided output %r", cmdline, stdout)
            raise MariaDBDumpError(
                "Failed to determine mariadb-dump version for %s" % command
            )

    def __init__(
        self,
        defaults_file,
        cmd_path="mariadb-dump",
        extra_defaults=False,
        mock_env=None,
    ):
        if not os.path.exists(cmd_path):
            raise MariaDBDumpError("'%s' does not exist" % cmd_path)
        self.cmd_path = cmd_path
        self.defaults_file = defaults_file
        self.extra_defaults = extra_defaults
        self._version = self.get_version(cmd_path)
        self.options = []
        self.mock_env = mock_env

    @property
    def version(self):
        """Return the version tuple (major, minor, patch)"""
        return self._version

    @property
    def version_str(self):
        """Return the version as a string (e.g. '10.5.8')"""
        return ".".join(str(d) for d in self._version)

    def set_options_from_config(self, config, bin_log_active=False):
        """Set options from the config dictionary."""
        config_options = []
        # Boolean options
        for key, option in [
            ("flush-logs", "--flush-logs"),
            ("flush-privileges", "--flush-privileges"),
            ("dump-routines", "--routines"),
            ("dump-events", "--events"),
            ("dump-history", "--dump-history"),
            ("order-by-size", "--order-by-size"),
        ]:
            if config[key]:
                config_options.append(option)

        # Handle max-allowed-packet
        if config["max-allowed-packet"]:
            config_options.append(
                f"--max-allowed-packet={config['max-allowed-packet']}"
            )

        # Handle bin-log-position
        if config["bin-log-position"]:
            if not bin_log_active:
                raise MariaDBDumpError(
                    "bin-log-position requested but bin-log on server not active"
                )
            config_options.append("--master-data=2")

        # Add additional options and validate
        for option in config_options + config["additional-options"]:
            if not option:
                continue
            if option in self.options:
                LOG.warning("mariadb-dump option '%s' already requested.", option)
            self.options.append(option)
            try:
                self._check_option(option, config["additional-options"])
                LOG.info("Using mariadb-dump option %s", option)
            except MariaDBDumpOptionError as exc:
                LOG.warning(str(exc))

    def _check_option(self, option, additional_options):
        """Checks and validates certain options we care about"""
        try:
            option, arg = OPTION_ARG_CRE.search(option).groups()
        except AttributeError:
            raise MariaDBDumpOptionError("Unparseable option '%s'" % option)

        if option in additional_options:
            raise MariaDBDumpOptionError("User supplied option '%s'" % option)

        required_version = CHECK_VERSION_OPTIONS.get(option)
        if required_version and self.version < required_version:
            raise MariaDBDumpOptionError(
                "Option %r requires minimum version %s"
                % (
                    option,
                    ".".join(str(d) for d in required_version),
                ),
            )

        pattern = CHECK_OPTION_ARG_PATTERNS.get(option)
        if pattern and not re.match(pattern, arg):
            if option == "--master-data":
                raise MariaDBDumpOptionError(
                    "Argument to --master-data must be 1 or 2 not %r" % arg
                )
            raise MariaDBDumpOptionError(
                "Invalid argument to option '%s': %r" % (option, arg)
            )

    def run(self, databases, stream, additional_options=None):
        """Run mariadb-dump with the options configured on this instance"""
        if not hasattr(stream, "fileno"):
            raise MariaDBDumpError("Invalid output stream")

        if not databases:
            raise MariaDBDumpError("No databases specified to backup")

        # Build the command arguments
        args = [self.cmd_path]

        # Add defaults file if specified
        if self.defaults_file:
            prefix = "defaults-extra" if self.extra_defaults else "defaults"
            args.append(f"--{prefix}-file={self.defaults_file}")

        # Add options derived from config
        args.extend(self.options)

        # Add additional options when called from base.start()
        if additional_options:
            args.extend(additional_options)

        # Handle database arguments
        if databases is ALL_DATABASES:
            args.append("--all-databases")
        else:
            args.extend(["--databases"] if len(databases) > 1 else [])
            args.extend(databases)

        if self.mock_env:
            LOG.info("Dry Run: %s", subprocess.list2cmdline(args))
            popen = self.mock_env.mocked_popen
        else:
            LOG.info("Executing: %s", subprocess.list2cmdline(args))
            popen = subprocess.Popen
        errlog = TemporaryFile()
        pid = popen(
            args, stdout=stream.fileno(), stderr=errlog.fileno(), close_fds=True
        )
        status = pid.wait()
        try:
            errlog.flush()
            errlog.seek(0)
            for line in errlog:
                LOG.error("%s[%d]: %s", self.cmd_path, pid.pid, line.rstrip())
        finally:
            errlog.close()
        if status != 0:
            raise MariaDBDumpError(
                "mariadb-dump exited with non-zero status %d" % pid.returncode
            )
