import os
import logging
from holland import __version__
from holland.cli.config import load_global_config
from holland.cli.log import configure_logging, configure_basic_logger
from holland.cli.cmd import ArgparseCommand, argument, CommandNotFoundError

HOLLAND_BANNER = """
Holland Backup v%s
Copyright (c) 2008-2010 Rackspace US, Inc.
More info available at http://hollandbackup.org

[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]]       [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]
[[[[[[[]]]]]]] [[[[[[[]]]]]]]

""" % __version__

LOG = logging.getLogger(__name__)

configure_basic_logger()

class HollandCli(ArgparseCommand):
    """Main holland command interface"""

    name = 'holland'

    summary = 'Holland command line'

    description = HOLLAND_BANNER

    arguments = [
        argument('--config', '-c', default='/etc/holland/holland.conf'),
        argument('--log-level', '-l'),
        argument('subcommand', nargs='?'),
        argument('args', nargs='...'),
    ]

    def __init__(self, name):
        ArgparseCommand.__init__(self, name)
        self.configure(None)

    def execute(self, opts, parser):

        try:
            config = load_global_config(opts.config)
        except IOError, exc:
            self.stderr("Failed to load config file %s: %s", opts.config, exc)
            return 1

        if opts.log_level:
            config['logging']['level'] = \
            logging._levelNames[opts.log_level.upper()]
        if config['holland']['umask'] is not None:
            os.umask(config['holland']['umask'])
        if config['holland']['tmpdir']:
            os.environ['TMPDIR'] = config['holland']['tmpdir']
        if config['holland']['path']:
            os.environ['PATH'] = config['holland']['path']
        configure_logging(config['logging'])

        if not opts.subcommand:
            parser.print_help()
            opts.subcommand = 'list-commands'

        self.configure(config)
        try:
            return self.chain(opts.subcommand, opts.args)
        except CommandNotFoundError, exc:
            self.stderr('Failed to load command "%s"', opts.subcommand)
            return 1
        except: # unexpected command failure
            self.stderr('Unexpected exception while running command "%s"',
                        opts.subcommand)
            import traceback
            traceback.print_exc()
            return 1
        return 1

holland = HollandCli('holland')
