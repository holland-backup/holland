import os, sys
import optparse
import logging
from holland.core.plugin import iter_entry_points, get_distribution
from holland.core.util.bootstrap import bootstrap
from holland.core.command import run
from holland.core.config.checks import is_logging_level

HOLLAND_VERSION = get_distribution('holland').version
HOLLAND_BANNER = """
Holland Backup v%s
Copyright (c) 2008-2016 Rackspace US, Inc.
More info available at http://hollandbackup.org

[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]]       [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]

""" % HOLLAND_VERSION

LOGGER = logging.getLogger(__name__)

## global parser
parser = optparse.OptionParser(add_help_option=False,version=HOLLAND_BANNER)
parser.add_option('-h', '--help', action='store_true',
                  help="Show help")
parser.add_option('-v', '--verbose', action='store_const', const='info',
                    dest='log_level',
                    help="Log verbose output")
parser.add_option('-d', '--debug', action='store_const', const='debug',
                    dest='log_level',
                    help="Log debug output")
parser.add_option('-c', '--config-file', metavar="<file>",
                  help="Read configuration from the given file")
parser.add_option('-q', '--quiet',  action='store_true',
                  help="Don't log to console")
parser.add_option('-l', '--log-level', type='choice', metavar='<log-level>',
                  choices=['critical', 'error','warning','info', 'debug'],
                  help="Specify the log level. "
                       "One of: critical,error,warning,info,debug")
parser.set_defaults(log_level=None,
                    quiet=False,
                    config_file=os.getenv('HOLLAND_CONFIG',
                                          '/etc/holland/holland.conf')
                   )
parser.disable_interspersed_args()

# main entrypoint for holland's cmdshell 'hl'
def main():
    opts, args = parser.parse_args(sys.argv[1:])

    logging.raiseExceptions = bool(opts.log_level == 'debug')

    if opts.log_level:
        opts.log_level = is_logging_level(opts.log_level)

    if not args:
        args = ['help']

    if opts.help or args[0] == 'help':
        if args[0] == 'help':
            args = args[1:]
        return run(['help'] + args)

    # Bootstrap the environment
    bootstrap(opts)

    LOGGER.info("Holland %s started with pid %d", HOLLAND_VERSION, os.getpid())
    return run(args)
