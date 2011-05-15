"""
    holland.cli.cmd.base
    ~~~~~~~~~~~~~~~~~~~~

    Holland CLI Command API

    :copyright: 2008-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import os, sys
import logging
from textwrap import dedent
from argparse import RawDescriptionHelpFormatter
from holland.core import BasePlugin, iterate_plugins
from holland.cli.cmd.util import SafeArgumentParser, ArgparseError
from holland.cli.cmd.error import CommandNotFoundError

LOG = logging.getLogger(__name__)

class BaseCommand(BasePlugin):
    """Base Command class for the Holland CLI

    A ``BaseCommand`` instance is callable and will be called with a list of
    command line args.  Subclasses should override ``__call__(args)`` and
    implement the actual command
    """

    #: Name of this command
    #: :type: str
    name = ''

    #: Textual summary of this command
    #: :type: str
    summary = ''

    #: Textual description of this command
    #: :type: str
    description = ''

    #: name aliases this command is also known by
    aliases = ()

    def __init__(self, name):
        BasePlugin.__init__(self, name)
        self.parent = None
        self.config = None

    #@classmethod
    def debug(cls, fmt, *args, **kwargs):
        """Writing a debugging message to the log"""
        LOG.debug(fmt, *args, **kwargs)
    debug = classmethod(debug)

    #@classmethod
    def stderr(cls, fmt, *args):
        """Write a message to stderr

        This logs via the python logging module
        at INFO verbosity

        :param fmt:  message format
        :param args: message arguments
        """
        print >>sys.stderr, fmt % args
    stderr = classmethod(stderr)

    #@classmethod
    def stdout(cls, fmt, *args):
        """Write a message to stdout

        This logs via the python logging module
        at INFO verbosity
        """
        print >>sys.stdout, fmt % args
    stdout = classmethod(stdout)

    def setup(self, parent):
        """Link this command with its parent command

        Only called on a subcommand - not the parent
        HollandCli instance.

        :param parent: parent ``BaseCommand`` instance
        """
        self.parent = parent

    def configure(self, config):
        """Configure this command

        This provides this command with the global
        config

        :param config: global holland.conf config
        """
        self.config = config

    def help(self):
        """Text documenting this command"""
        raise NotImplementedError()

    def load(self, name):
        """Load a command by name

        :param name: name of the command to load
        :returns: BaseCommand instance
        :raises: CommandNotFoundError
        """
        for cmd in list(iterate_plugins('holland.commands')):
            if cmd.matches(name):
                cmd.setup(self)
                cmd.configure(self.config)
                return cmd
        raise CommandNotFoundError(name)

    def chain(self, name, args):
        """Dispatch to another command

        :param name: name of the command to dispatch to
        :param args: command line args to pass to cmd
        :returns: int -- exit status of command
        """
        cmd = self.load(name)
        return cmd(args)

    def __call__(self, args):
        """Run this command

        This method must be overriden in a subclass
        """
        raise NotImplementedError()

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __lt__(self, other):
        return self.name < other.name

    def matches(self, name):
        """Check whether this command should match a given name"""
        return self.name == name or name in self.aliases

    def plugin_info(self):
        """Provide plugin info about this command

        This method should return a dictionary listing a minimum of the
        following attributes:

          * name          - short one word name of this command
          * summary       - one line summary of this command
          * description   - longer description of this command
          * author        - author of this command in name [<email>] format
          * version       - version of this command
          * api_version   - version of holland this command is intended to work
                            with

        :returns: dict
        """
        raise NotImplementedError()

def argument(*args, **kwargs):
    """Simple wrapper for argparse parameters"""
    return (args, kwargs)

class ArgparseCommand(BaseCommand):
    """Command implementation that parses arguments with argparse

    Subclasses of ``ArgparseCommand`` should override the
    ``execute(namespace, parser)`` method.  ``namespace`` will be
    an argparse ``Namespace`` instance and parser will be the original
    ``ArgumentParser`` instance used by this command.
    """

    #: list of arguments to ArgumentParser.add_argument
    arguments = [
    ]

    #: optional epilog - passed to ArgumentParser() constructor
    epilog = None

    _add_help = True

    def __init__(self, *args, **kwargs):
        super(ArgparseCommand, self).__init__(*args, **kwargs)

    def create_parser(self):
        """Build the ArgparseParser used by this command

        By default this creates an instance of
        ``holland.cli.cmd.util.SafeArgumentParser`` -
        an ArgumentParser that raises an exception on error rather than
        calling sys.exit()

        :returns: ArgumentParser instance
        """
        fmt_cls = RawDescriptionHelpFormatter
        parser = SafeArgumentParser(description=dedent(self.description),
                                    prog=self.name,
                                    epilog=dedent(self.epilog or ''),
                                    formatter_class=fmt_cls,
                                    add_help=False)
        if self._add_help:
            parser.add_argument('--help', '-h', action='store_true')
        for _args, _kwargs in self.arguments:
            parser.add_argument(*_args, **_kwargs)
        return parser

    def __call__(self, args=None):
        parser = self.create_parser()

        try:
            optns = parser.parse_args(args)
        except ArgparseError, exc:
            if exc.message:
                self.stderr("%s", exc.message)
                self.stderr("%s", parser.format_help())
            return 1
        if getattr(optns, 'help', False):
            self.stderr("%s", self.help())
            return 1
        return self.execute(optns, parser)

    def execute(self, namespace, parser):
        """Execute a command

        Subclasses should override this method and this will automatically be
        called with the result of parse_args() when this command is called
        """
        raise NotImplementedError()

    def help(self):
        """Format help via ArgumentParser"""
        return self.create_parser().format_help()

    def plugin_info(self):
        """Provide plugin info about this command

        This method should return a dictionary listing a minimum of the
        following attributes:

          * name          - short one word name of this command
          * summary       - one line summary of this command
          * description   - longer description of this command
          * author        - author of this command in name [<email>] format
          * version       - version of this command
          * api_version   - version of holland this command is intended to work
                            with

        :returns: dict
        """
        raise NotImplementedError()
