"""
Pluggable command support
"""

import os
import sys
import argparse
from argparse import RawTextHelpFormatter
import logging
from distutils.version import LooseVersion
from pkg_resources import get_distribution

LOG = logging.getLogger(__name__)
HOLLAND_VERSION = get_distribution("holland").version
HOLLAND_BANNER = (
    """
Holland Backup v%s
Copyright (c) 2008-2018 Rackspace US, Inc.
More info available at http://hollandbackup.org

[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]]       [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]

"""
    % HOLLAND_VERSION
)

HOLLAND_CONF = "/etc/holland/holland.conf"
if sys.platform.startswith("freebsd"):
    HOLLAND_CONF = "/usr/local" + HOLLAND_CONF

## global parser
PARSER = argparse.ArgumentParser(description=HOLLAND_BANNER, formatter_class=RawTextHelpFormatter)
# PARSER.add_argument('-h', '--help', action='store_true',
#                    help="Show help")
PARSER.add_argument(
    "-v",
    "--verbose",
    action="store_const",
    const="info",
    dest="log_level",
    help="Log verbose output",
)
PARSER.add_argument(
    "-d", "--debug", action="store_const", const="debug", dest="log_level", help="Log debug output"
)
PARSER.add_argument(
    "-c", "--config-file", metavar="<file>", help="Read configuration from the given file"
)
PARSER.add_argument("-q", "--quiet", action="store_true", help="Don't log to console")
PARSER.add_argument(
    "-l",
    "--log-level",
    metavar="<log-level>",
    choices=["critical", "error", "warning", "info", "debug"],
    help="Specify the log level. " "One of: critical,error,warning,info,debug",
)
PARSER.add_argument("--version", action="version", version=HOLLAND_VERSION)
PARSER.set_defaults(
    log_level="info", quiet=False, config_file=os.getenv("HOLLAND_CONFIG", HOLLAND_CONF)
)
SUBPARSER = PARSER.add_subparsers(dest="command")


class Command(object):
    """Base Command class for implementing pluggable
    commmands.

    User commands typically inherit this class and
    implement an appropriate run(self, cmdname, opts, [args...])
    and this parent class will discover the acceptable arguments
    based on the run() method signature

    To get this working with argparse I had to split up arg, and karg.
    This list need to be the same size for this to work correctly.
    """

    name = None
    aliases = []
    nargs = 0
    args = []
    kargs = []
    description = " "

    def __init__(self):
        if LooseVersion(argparse.__version__) < LooseVersion("1.4.0"):
            self.optparser = SUBPARSER.add_parser(
                self.name, help="%s %s" % (self.name, self.description), description=self.name
            )
            self.alias_parser = []
            for alias in self.aliases:
                self.alias_parser.append(
                    SUBPARSER.add_parser(
                        alias, help="Alias to %s" % self.name, description=self.name
                    )
                )
            for parser in self.alias_parser:
                for counter, arg in enumerate(self.args):
                    parser.add_argument(*arg, **self.kargs[counter])
        else:
            self.optparser = SUBPARSER.add_parser(
                self.name,
                help="%s %s" % (self.name, self.description),
                aliases=self.aliases,
                description=self.name,
            )

        for counter, arg in enumerate(self.args):
            self.optparser.add_argument(*arg, **self.kargs[counter])

    def run(self, cmd, opts, *args):
        """
        This should be overridden by subclasses
        """

    def dispatch(self, opts, args):
        """
        Dispatch arguments to this command
        Parses the arguments through this command's
        option parser and delegates to self.run(*args)
        """
        try:
            return self.run(self.optparser.prog, opts, *args)
        except KeyboardInterrupt:
            raise
        except TypeError as ex:
            LOG.error("Failed comamnd %s': %s", self.optparser.prog, ex)
            return os.EX_SOFTWARE
        except BaseException as ex:
            LOG.error(
                "Uncaught exception while running command '%s': %r",
                self.optparser.prog,
                ex,
                exc_info=True,
            )
            return os.EX_SOFTWARE
