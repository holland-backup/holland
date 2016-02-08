"""
Commvault command entry point
"""
import holland.core
import sys, os
import logging
import resource

from holland.core.util.bootstrap import bootstrap
from holland.commands.backup import Backup
from holland.core.command import run
from holland.core.cmdshell import HOLLAND_VERSION
from holland.core.util.fmt import format_loglevel
from argparse import ArgumentParser, Action
# The janky arguments Commvault throws at us
# http://documentation.commvault.com/commvault/release_8_0_0/books_online_1/english_us/features/pre_post/prepost_process.htm
# http://documentation.commvault.com/commvault/release_7_0_0/books_online_1/english_us/features/pre_post/prepost_process.htm
#CV_ARGS = ("-bkplevel",
#           "-attempt",
#           "-status",
#           "-job",
#           "-vm"
#           "-cn")

class ArgList(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        arg_list = [x.strip() for x in value.split(',')]
        setattr(namespace, self.dest, arg_list)

def main():
    # For some reason (take a wild guess) Commvault has decided that
    # their long options will take the form of '-option' not the standard
    # '--option'.


    # Always set HOME to '/root', as the commvault environment is bare
    os.environ['HOME'] = '/root'
    os.environ['TMPDIR'] = '/tmp'
    # ensure we do not inherit commvault's LD_LIBRARY_PATH
    os.environ.pop('LD_LIBRARY_PATH', None)

    argv = sys.argv[1:]

    parser = ArgumentParser()
    parser.add_argument("--config-file", "-c", metavar="<file>",
                        help="Read configuration from the given file")
    parser.add_argument("--log-level", "-l", type='choice',
                        choices=['critical','error','warning','info',
                                 'debug'],
                        help="Specify the log level."
                       )
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Don't log to console")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    parser.add_argument("--bksets", "-b", metavar="<bkset>,<bkset>...",
                        help="only run the specified backupset",
                        default=[], action=ArgList)

    parser.add_argument("-bkplevel", type=int)
    parser.add_argument("-attempt", type=int)
    parser.add_argument("-status", type=int)
    parser.add_argument("-job", type=int)
    parser.add_argument("-vm")
    parser.add_argument("-cn")
    parser.set_defaults(
        config_file=os.getenv('HOLLAND_CONFIG') or '/etc/holland/holland.conf',
        verbose=False,
    )

    args, largs = parser.parse_known_args(argv)

    bootstrap(args)

    logging.info("Holland (commvault agent) %s started with pid %d",
                 HOLLAND_VERSION, os.getpid())
    # Commvault usually runs with a very low default limit for nofile
    # so a best effort is taken to raise that here.
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (262144, 262144))
        logging.debug("(Adjusted ulimit -n (RLIMIT_NOFILE) to %d)", 262144)
    except (ValueError, resource.error), exc:
        logging.debug("Failed to raise RLIMIT_NOFILE: %s", exc)

    if args.log_level:
        args.log_level = format_loglevel(opts.log_level)

    if run(['backup'] + args.bksets):
        return 1
    else:
        return 0
