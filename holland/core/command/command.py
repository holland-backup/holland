"""
Pluggable command support
"""
from __future__ import print_function 

import os
import sys
import re
import optparse
import textwrap
import logging
# from types import StringTypes
from inspect import getargspec, getdoc
import logging
from holland.core.util.template import Template

LOGGER = logging.getLogger(__name__)


def option(*args, **kwargs):
    return optparse.make_option(*args, **kwargs)

class StopOptionProcessing(Exception):
    pass


class _OptionParserEx(optparse.OptionParser):
    def __init__(self, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        #self.remove_option('--help')

    def error(self, msg):
        raise optparse.OptParseError(msg)

    def exit(self, status=0, msg=None):
        if not status:
            raise StopOptionProcessing(msg)
        else:
            # TODO: don't lose status info here
            raise optparse.OptParseError(msg)
 
option = optparse.make_option

class Command(object):
    """Base Command class for implementing pluggable
    commmands.

    User commands typically inherit this class and 
    implement an appropriate run(self, cmdname, opts, [args...])
    and this parent class will discover the acceptable arguments
    based on the run() method signature
    """

    name = None
    aliases = [
    ]

    options = [
    ]

    description = ''

    def __init__(self):
        help_fmt = optparse.IndentedHelpFormatter()
        self.optparser = _OptionParserEx(prog=self.name,
                                         add_help_option=False,
                                         formatter=help_fmt)
        self.optparser.add_option('--help', '-h', action='store_true',
                                  help='show this help message and exit')
        self.optparser.add_options(self.options)

    def format_cmd_options(self):
        """
        Format the options this command supports

        Default behavior is to delegate to format_option_help() of
        the associated OptionParser instance for this command
        """
        return self.optparser.format_option_help()

    def format_arg(self, arg):
        """
        Format an individual argument this command supports
        """
        return arg.replace('_', '-')

    def format_varargs(self, arg):
        """
        Format how variable arguments (\*args) are displayed
        """
        return '[%s...]' % self.format_arg(arg)

    def _check_argspec(self, args, varargs, varkw, defaults):
        for arg in args:
            if not isinstance(arg, str):
                raise AssertionError('Tuple arguments are not supported')
        if varkw:
            raise AssertionError('Keyword arguments are not supported')

    def format_cmd_args(self):
        """
        Format all the arguments accepted by this command

        Defers to self.format_arg and self.format_varargs
        """

        args, varargs, varkw, defaults = getargspec(self.run)
        self._check_argspec(args, varargs, varkw, defaults)
        args = args[3:]
        specs = []
        if defaults:
            firstdefault = len(args) - len(defaults)
        for i in range(len(args)):
            spec = self.format_arg(args[i])
            if defaults and i >= firstdefault:
                spec = '[' + spec + ']'
            specs.append(spec)
        if varargs is not None:
            specs.append(self.format_varargs(varargs))
        return ' '.join(specs)

    def usage(self):
        """
        Format this command's usage string
        """
        tpl = Template("Usage: ${cmd_name} ${options}${cmd_args}")
        return tpl.safe_substitute(cmd_name=self.name,
                                   options=self.options and "[options] " or "",
                                   cmd_args=self.format_cmd_args())

    def reformat_paragraphs(self, str):
        from textwrap import wrap
        paragraphs = []
        buffer = ''
        for line in str.splitlines():
            if not line and buffer:
                paragraphs.append("\n".join(wrap(buffer, 65)))
                buffer = ''
            else:
                buffer += line
        if buffer:
            paragraphs.append(buffer)

        return "\n\n".join(paragraphs)

    def help(self):
        """
        Format this command's help output

        Default is to use the class' docstring as a 
        template and interpolate the name, options and 
        arguments
        """
        usage_str = getdoc(self) or ''
        usage_str = self.reformat_paragraphs(usage_str)
        cmd_name = self.name
        cmd_opts = self.format_cmd_options()
        cmd_args = self.format_cmd_args()
        help_str = Template(usage_str).safe_substitute(cmd_name=cmd_name,
                                                   cmd_option_list=cmd_opts,
                                                   cmd_args=cmd_args,
                                                   cmd_usage=self.usage()
                                                   ).rstrip()
        return re.sub(r'\n\n+', r'\n\n', help_str)

    def parse_args(self, argv):
        """
        Parse the options for this command
        """
        self.optparser.prog = argv.pop(0)

        opts, args = self.optparser.parse_args(argv)
        return opts, args

    def dispatch(self, argv):
        """
        Dispatch arguments to this command

        Parses the arguments through this command's
        option parser and delegates to self.run(\*args)
        """
        run_args, run_varargs, run_varkw, run_defaults = getargspec(self.run)
        try:
            opts, args = self.parse_args(argv)
        except StopOptionProcessing as e:
            return 1
        except optparse.OptParseError as e:
            print(self.usage(), file=sys.stderr)
            print()
            print("%s: error: %s" % (self.name, e), file=sys.stderr)
            return 1

        if opts.help:
            print(self.help())
            return os.EX_USAGE

        cmd_name = self.optparser.prog

        if len(args) > len(run_args[3:]) and not run_varargs:
            print("Error: %s only accepts %d arguments but %d were provided" % ( (self.name, len(run_args[3:]), len(args))), file=sys.stderr)
            print(self.help())
            return os.EX_USAGE

        num_req = len(run_defaults or []) or 0
        if len(args) < len(run_args[3:-num_req or None]):
            print("Failed: %s requires %d arguments required, %d provided" % (cmd_name,len(run_args[3:-num_req or None]), len(args)), file=sys.stderr)
            print(self.help())
            return os.EX_USAGE
        try:
            return self.run(self.optparser.prog, opts, *args)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            LOGGER.error("Uncaught exception while running command '%s': %r", cmd_name, e, exc_info=True)
            return os.EX_SOFTWARE


    def run(self, cmd, opts, *args):
        """
        This should be overridden by subclasses
        """
        pass

    def __cmp__(self, other):
        """
        Sort this commmand alphabetically
        """
        # Useful for sorting a list of commands alphabetically
        return cmp(self.name, other.name)
