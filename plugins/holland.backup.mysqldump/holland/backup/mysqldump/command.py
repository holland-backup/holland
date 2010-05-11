"""mysqldump support"""

import os
import re
import errno
import logging
import subprocess
from tempfile import TemporaryFile

LOG = logging.getLogger(__name__)

ALL_DATABASES = object()

def check_master_data(version, arg):
    """Validate --master-data against a mysqldump version"""
    if version < (4, 1, 8) and arg:
        raise MyOptionError("--master-data only takes an argument in MySQL "
                            ">= 4.1.8")
    else:
        if arg:
            try:
                value = int(arg)
                assert value in (1, 2)
            except ValueError:
                raise MyOptionError("Invalid argument to --master-data: %r" % \
                                    arg)
            except AssertionError:
                raise MyOptionError("Argument to --master-data must be 1 or 2 "
                                    "not %r" % arg)

class MySQLDumpError(Exception):
    """Excepton class for MySQLDump errors"""

class MyOptionError(Exception):
    """Exception class for MySQL Option validation"""

class MyOptionChecker(object):
    """Container for adding and validating multiple options"""
    OPTION_ARG_CRE = re.compile(r'^(--[^=]+)(?:=(.+))?$', re.UNICODE)

    def __init__(self, version):
        self.version = version
        self._options = {}

    def check_option(self, option):
        """Check an option"""
        try:
            option, arg = self.OPTION_ARG_CRE.search(option).groups()
        except AttributeError:
            raise MyOptionError("Unsupported option %r" % option)

        option = option.replace('_', '-')

        if option not in self._options:
            raise MyOptionError("Unsupported option %r" % option)
        my_option = self._options[option]
        my_option.check(self.version, arg)

    def add_option(self, my_option):
        """Add an option to this validator"""
        self._options[my_option.option] = my_option


class MyOption(object):
    """General MySQL command option"""
    def __init__(self, option, min_version=None, arg=None):
        self.option = option
        self.min_version = min_version
        self.arg = arg

    def check(self, version, arg=None):
        """Check this option against the particular mysql version
        and given the particular argument to the option.
        """
        self.check_version(version)
        self.check_arg(version, arg)

    def check_arg(self, version, arg):
        """Check the given argument against this option.
        """
        if isinstance(self.arg, basestring):
            return re.match(self.arg, arg, re.UNICODE) is not None
        elif callable(self.arg):
            return self.arg(version, arg)
        elif arg:
            raise MyOptionError("Invalid arg constraint %r" % self.arg)

    def check_version(self, version):
        """Check the given command version against the version required by
        this option"""
        if self.min_version and version < self.min_version:
            raise MyOptionError("Option %r requires minimum version %s" % \
                                (self.option,
                                 '.'.join([str(x) for x in self.min_version])
                                )
                            )

# XXX: support --skip-* for all options as well
MYSQLDUMP_OPTIONS = [
    # boolean options
    MyOption('--flush-logs'),
    MyOption('--flush-privileges', min_version=(5,0,26)),
    MyOption('--force'),
    MyOption('--hex-blob', min_version=(4,1,8)),
    MyOption('--add-drop-database'),
    MyOption('--no-autocommit'),
    MyOption('--delete-master-logs'),
    MyOption('--compress'),
    MyOption('--order-by-primary', min_version=(4,1,8)),
    MyOption('--insert-ignore', min_version=(4,1,12)),
    MyOption('--routines', min_version=(5,0,13)),
    MyOption('--events', min_version=(5,1,8)),
    MyOption('--max-allowed-packet', arg='\w'),

    # options that take arguments
    MyOption('--default-character-set', arg='\w'),
    MyOption('--master-data', arg=check_master_data),

    # lock modes
    MyOption('--single-transaction', (4,0,2)),
    MyOption('--lock-all-tables', min_version=(4,1,8)),
    MyOption('--lock-tables'),

    # misc
    MyOption('--skip-dump-date', min_version=(5,1,23)),
]

def mysqldump_version(command):
    """Return the version of the given mysqldump command"""
    args = [
        command,
        '--no-defaults',
        '--version',
    ]
    LOG.debug("Executing: %s", subprocess.list2cmdline(args))
    try:
        output = subprocess.Popen(args,
                                  stdout=subprocess.PIPE).communicate()[0]
    except OSError, exc:
        if exc.errno == ENOENT:
            raise MySQLDumpError("'%s' does not exist" % command)
        else:
            raise MySQLDumpError("Error[%d:%s] when trying to run '%s'" % \
                    (exc.errno, errno.errocode[exc.errno], command))

    try:
        return tuple([int(digit) for digit in
                        re.search(r'(\d+)[.](\d+)[.](\d+)', output).groups()])
    except AttributeError, exc:
        raise MySQLDumpError("Failed to determine mysqldump version for %s" % \
                             command)

class MySQLDump(object):
    """mysqldump command runner"""
    def __init__(self,
                 defaults_file,
                 cmd_path='mysqldump',
                 extra_defaults=False):
        if not os.path.exists(cmd_path):
            raise MySQLDumpError("'%s' does not exist" % cmd_path)
        self.cmd_path = cmd_path
        self.defaults_file = defaults_file
        self.extra_defaults = extra_defaults
        self.version = mysqldump_version(cmd_path)
        self.version_str = u'.'.join([str(digit) for digit in self.version])
        self.mysqldump_optcheck = MyOptionChecker(self.version)
        for optspec in MYSQLDUMP_OPTIONS:
            self.mysqldump_optcheck.add_option(optspec)
        self.options = []

    def add_option(self, option):
        """Add an option to this mysqldump instance, to be used
        when mysqldump is actually run via the instances .run() method
        """
        if option in self.options:
            LOG.warn("mysqldump option '%s' already requested.", option)
        self.options.append(option)
        self.mysqldump_optcheck.check_option(option)

    def run(self, databases, stream, additional_options=None):
        """Run mysqldump with the options configured on this instance"""
        if not hasattr(stream, 'fileno'):
            raise MySQLDumpError("Invalid output stream")

        if not databases:
            raise MySQLDumpError("No databases specified to backup")

        args = [ self.cmd_path, ]

        if self.defaults_file:
            if self.extra_defaults:
                args.append('--defaults-extra-file=%s' % self.defaults_file)
            else:
                args.append('--defaults-file=%s' % self.defaults_file)

        args.extend([str(opt) for opt in self.options])

        if additional_options:
            args.extend(additional_options)

        if databases is ALL_DATABASES:
            args.append('--all-databases')
        else:
            if len(databases) > 1:
                args.append('--databases')
            args.extend(databases)

        LOG.info("Executing: %s", subprocess.list2cmdline(args))
	errlog = TemporaryFile()
        pid = subprocess.Popen(args, 
                               stdout=stream.fileno(), 
                               stderr=errlog.fileno(), 
                               close_fds=True)
        status = pid.wait()
        try:
            errlog.flush()
            errlog.seek(0)
            for line in errlog:
                LOG.error("%s [%d]: %s", self.cmd_path, pid.pid, line.rstrip())
        finally:
            errlog.close()
	if status != 0:
            raise MySQLDumpError("mysqldump exited with non-zero status %d" % \
                                 pid.returncode)
