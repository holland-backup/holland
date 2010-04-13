"""Command Line Interface"""

import os
import sys
import csv
import locale
import getpass
import logging
import warnings
from StringIO import StringIO
from optparse import OptionParser, OptionGroup
from core import dry_run, start

def add_general_options(option_parser):
    """Add general options to the given OptionParser"""
    option_parser.add_option('--stop-slave',
                             action='store_true',
                             help="Stop the slave")
    option_parser.add_option('--file-per-database',
                             action='store_true',
                             help='Backup each database to a separate file.')
    option_parser.add_option('--compression',
                             metavar='command',
                             default='',
                             help="Compression program to use.")
    option_parser.add_option('--replication',
                             action='store_true',
                             help="Acquire replication information")
    option_parser.add_option('--extra-options',
                             metavar='options',
                             default='',
                             help="Extra options to pass to mysqldump")
    option_parser.add_option('--dry-run',
                             action='store_true',
                             default=False,
                             help="Run through the steps of backing up, but don't "
                                  "actually run mysqldump")
    option_parser.add_option('--debug',
                             action='store_true',
                             default=False,
                             help="Enable debug logging")
 
def add_auth_options(option_parser):
    """Add MySQL authentication options to the given OptionParser"""
    mysql_auth_options = OptionGroup(option_parser,
                                     "MySQL Connection Options",
                                     "These options affect how the program "
                                     "connects to the MySQL server")
    mysql_auth_options.add_option('--user', '-u',
                                  metavar='user',
                                  help="User for login")
    mysql_auth_options.add_option('--password', '-p',
                                  action='store_true',
                                  default=False,
                                  help="Prompt for password at tty")
    mysql_auth_options.add_option('--host', '-h',
                                  metavar='host',
                                  help="Connect to host")
    mysql_auth_options.add_option('--port', '-P',
                                  metavar='port',
                                  type='int',
                                  help="Port number to use for connection")
    mysql_auth_options.add_option('--socket', '-S',
                                  metavar='socket',
                                  help='Socket file to use for connection')
    mysql_auth_options.add_option('--defaults-file',
                                  metavar='defaults-file',
                                  default=os.path.expanduser('~/.my.cnf'),
                                  help="Only read default options from the "
                                       "given file")
    option_parser.add_option_group(mysql_auth_options)


def add_filter_options(option_parser):
    """Add database/table filtering options to the given OptionParser"""
    filter_options = OptionGroup(option_parser,
                                 "Filter Options",
                                 "These options will filter what's actually "
                                 "dumped")
    filter_options.add_option('--include-databases', '-d',
                              metavar='databases',
                              default=[],
                              action='append',
                              help="Include only the specified databases")
    filter_options.add_option('--exclude-databases', '-D',
                              metavar='databases',
                              default=[],
                              action='append',
                              help='Exclude the specified databases')
    filter_options.add_option('--include-tables', '-t',
                              metavar='tables',
                              default=[],
                              action='append',
                              help='Include only the specified tables.')
    filter_options.add_option('--exclude-tables', '-T',
                              metavar='tables',
                              default=[],
                              action='append',
                              help='Exclude the specified tables.')
    filter_options.add_option('--include-engines', '-e',
                              metavar='engines',
                              default=[],
                              action='append',
                              help="Include only the specified engines")
    filter_options.add_option('--exclude-engines', '-E',
                              metavar='engines',
                              default=[],
                              action='append',
                              help='Exclude the specified engines')
    option_parser.add_option_group(filter_options)
    
def main(args=None):
    """CLI script entry point"""
    warnings.showwarning = lambda *args, **kwargs: None
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    option_parser = OptionParser(add_help_option=False)
    option_parser.add_option('-?', '--help',
                             action='help')
    add_general_options(option_parser)
    add_auth_options(option_parser)
    add_filter_options(option_parser)

    if not args:
        args = sys.argv

    args = [unicode(arg, locale.nl_langinfo(locale.CODESET)) for arg in args]

    for arg in args:
        print "%r" % arg

    opts, args = option_parser.parse_args(args)

    if opts.debug:
        for handler in logging.root.handlers:
            logging.root.handlers.remove(handler)
        logging.basicConfig(level=logging.DEBUG)

    if opts.password:
        opts.password = getpass.getpass("Password:")

    if opts.replication:
        opts.extra_options += ' --master-data=2'

    filter_optgroup = option_parser.get_option_group('--include-databases')
    filter_options = filter_optgroup.option_list
    
    for opt in filter_options:
        filters = compile_filters(getattr(opts, opt.dest))
        setattr(opts, opt.dest, filters)

    if opts.dry_run:
        dry_run(opts.__dict__)
    else:
        start(opts.__dict__)

def compile_filters(filter_list):
    """Compile a list of comma-separated-values into a single flat list"""
    result = []
    for filter_str in filter_list:
        items = csv.reader(StringIO(filter_str.encode(locale.nl_langinfo(locale.CODESET))),
                           quotechar='`',
                           skipinitialspace=True).next()
        for item in items:
            result.append(unicode(item, locale.nl_langinfo(locale.CODESET)))
    return result

if __name__ == '__main__':
    sys.exit(main())
