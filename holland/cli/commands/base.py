"""Base command classes"""

import sys
import logging
from textwrap import dedent
from argparse import RawDescriptionHelpFormatter
from util import StreamWriter, SafeArgumentParser, ArgparseError

LOG = logging.getLogger(__name__)

class BaseCommand(object):
    """Basic command support"""
    def __init__(self, parent_parser=None, config=None):
        self.parent_parser = parent_parser
        self.config = config
        self.stderr = StreamWriter(sys.stderr)
        self.stdout = StreamWriter(sys.stdout)

    # name aliases this command is also known by
    aliases = ()

    #@property
    def name(self):
        """Main name of this command"""
        raise NotImplementedError()
    name = property(name)

    #@property
    def summary(self):
        """Simple one-line string summarizing this command"""
        raise NotImplementedError()
    summary = property(summary)

    #@property
    def description(self):
        """Text block describing this command"""
        raise NotImplementedError()
    description = property(description)

    #@property
    def help(self):
        """Text documenting this command"""
        raise NotImplementedError()
    help = property(help)

    def __call__(self, args, context=None):
        raise NotImplementedError()

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    #@classmethod
    def matches(cls, name):
        """Check whether this command should match a given name"""
        return cls().name == name or name in cls.aliases
    matches = classmethod(matches)

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
        formatter_class = RawDescriptionHelpFormatter
        self.parser = SafeArgumentParser(description=dedent(self.description),
                                         prog=self.name,
                                         epilog=dedent(self.epilog or ''),
                                         formatter_class=formatter_class,
                                         add_help=False)
        if self._add_help:
            self.parser.add_argument('--help', '-h', action='store_true')
        for _args, _kwargs in self.arguments:
            self.parser.add_argument(*_args, **_kwargs)

    def __call__(self, args=None):
        try:
            optns = self.parser.parse_args(args)
        except ArgparseError, exc:
            if exc.message:
                self.stderr("%s", exc.message)
                self.stderr("%s", self.parser.format_help())
            return 1
        if getattr(optns, 'help', False):
            self.stderr("%s", self.help())
            return 1
        return self.execute(optns)

    def execute(self, namespace):
        """Execute a command

        Subclasses should override this method and this will automatically be
        called with the result of parse_args() when this command is called
        """
        raise NotImplementedError()

    def help(self):
        """Format help via ArgumentParser"""
        return self.parser.format_help()
