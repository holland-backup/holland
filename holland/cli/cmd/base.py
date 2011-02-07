"""Base command classes"""

import sys
import logging
from textwrap import dedent
from argparse import RawDescriptionHelpFormatter
from holland.core import BasePlugin, iterate_plugins
from holland.cli.cmd.util import StreamWriter, SafeArgumentParser, ArgparseError
from holland.cli.cmd.error import CommandNotFoundError

LOG = logging.getLogger(__name__)

class BaseCommand(BasePlugin):
    """Basic command support"""

    #: Name of this command
    #: :type: str
    name = ''

    #: Textual summary of this command
    #: :type: str
    summary = ''

    #: Textual description of this command
    #: :type: str
    description = ''

    # name aliases this command is also known by
    aliases = ()

    def __init__(self, name):
        BasePlugin.__init__(self, name)
        self.parent = None
        self.config = None
        self.stderr = StreamWriter(sys.stderr)
        self.stdout = StreamWriter(sys.stdout)

    def setup(self, parent):
        """Link this command with its parent command

        Only called on a subcommand
        """
        self.parent = parent

    def configure(self, config):
        """Configure this command

        This provides this command with the global
        config
        """
        self.config = config

    def help(self):
        """Text documenting this command"""
        raise NotImplementedError()

    def load(self, name):
        """Load a command by name"""
        for cmd in list(iterate_plugins('holland.commands')):
            if cmd.matches(name):
                cmd.setup(self)
                cmd.configure(self.config)
                return cmd
        raise CommandNotFoundError(name)

    def chain(self, name, args):
        """Chain to another command using the given arguments"""
        cmd = self.load(name)
        return cmd(args)

    def __call__(self, args):
        raise NotImplementedError()

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __lt__(self, other):
        return self.name < other.name

    def matches(self, name):
        """Check whether this command should match a given name"""
        return self.name == name or name in self.aliases


def argument(*args, **kwargs):
    """Simple wrapper for argparse parameters"""
    return (args, kwargs)

class ArgparseCommand(BaseCommand):
    """Command implementation that parses arguments with argparse"""

    # list of arguments to ArgumentParser.add_argument
    arguments = [
    ]

    # optional epilog - passed to ArgumentParser() constructor
    epilog = None

    _add_help = True

    def __init__(self, *args, **kwargs):
        super(ArgparseCommand, self).__init__(*args, **kwargs)

    def create_parser(self):
        """Build the ArgparseParser used by this command

        By default this creates an instance of ``SafeArgumentParser`` -
        an ArgumentParser that raises an excepton on error rather than
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
