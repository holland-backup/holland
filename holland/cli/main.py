"""Main holland command"""

import os
import signal
import logging
from logging import _levelNames as log_levels
from holland import __version__
from holland.cli.config import load_global_config
import holland.cli.log as holland_logging
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

holland_logging.configure_warnings()
holland_logging.configure_basic_logger()

def terminate(signum, frame):
    """Terminate from SIGTERM cleanly"""
    LOG.debug("terminate(signum=%r, frame=%r)", signum, frame)
    raise SystemExit("Caught SIGTERM")

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
        """Execute the main holland command

        This will load the global config if it exists and
        dispatch to a subcommand if one is specified.

        If not subcommand is given this defaults to 'list-commands'
        and only prints the available commands.
        """
        try:
            config = load_global_config(opts.config)
        except IOError, exc:
            self.stderr("Failed to load config file %s: %s", opts.config, exc)
            return 1

        if opts.log_level:
            config['logging']['level'] = \
            log_levels[opts.log_level.upper()]
        if config['holland']['umask'] is not None:
            os.umask(config['holland']['umask'])
        if config['holland']['tmpdir']:
            os.environ['TMPDIR'] = config['holland']['tmpdir']
        if config['holland']['path']:
            os.environ['PATH'] = config['holland']['path']
        holland_logging.configure_logging(config['logging'])
        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGQUIT, terminate)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        if not opts.subcommand:
            parser.print_help()
            opts.subcommand = 'list-commands'

        self.configure(config)
        try:
            return self.chain(opts.subcommand, opts.args)
        except CommandNotFoundError, exc:
            self.stderr("'%s' is not a valid holland command. "
                        "See holland help for valid commands.", exc.name)
        except: # unexpected command failure
            self.stderr('Unexpected exception while running command "%s"',
                        opts.subcommand)
            import traceback
            traceback.print_exc()
        return 1

    def plugin_info(self):
        """Plugin info for the main holland command"""
        # this is not used as we do not expose the main script command as a
        # plugin, but included here anyway for documentation purposes
        return dict(
            author='Rackspace',
            name='holland',
            summary='Main holland script',
            description='''
            This is the main holland cli command as bundled
            with the holland backup framework.
            ''',
            version=__version__,
            api_version=__version__
        )
holland = HollandCli('holland')
