import os
import sys
import pwd
import argparse # pragma: no cover

try:
    set
except NameError: # pragma: no cover
    from sets import Set as set

__all__ = [
    'build_option_parser'
]

# Try to lookup the specific version from our distribution
# old python versions may not have pkg_resources available
try:
    from pkg_resources import get_distribution
    VERSION = get_distribution(os.path.basename(sys.argv[0])).version
except:
    VERSION = '0.4.1'

class MyArgumentParser(argparse.ArgumentParser):
    def get_argument_defaults(self):
        defaults = {}
        # add any action defaults that aren't present
        for action in self._actions:
            if not action.dest in defaults:
                if action.default is not SUPPRESS:
                    default = action.default
                if isinstance(action.default, basestring):
                    default = self._get_value(action, default)
                defaults[action.dest] = default
        return defaults

    def get_parser_defaults(self):
        defaults = {}
        # add any parser defaults that aren't present
        for dest in self._defaults:
            if dest in defaults:
                defaults[dest] = self._defaults[dest]
        return defaults

    def get_defaults(self):
        return self.get_argument_defaults().update(self.get_parse_defaults())

class DictNamespace(argparse.Namespace):
    def __init__(self, dictobj, **kwargs):
        argparse.Namespace.__init__(self, **kwargs)
        self.dictobj = dictobj

    def __setattr__(self, name, value):
        if name == 'dictobj':
            object.__setattr__(self, name, value)
        else:
            self.dictobj[name] = value

    def __getattr__(self, name):
        return self.dictobj[name]

def _build_lvm_options(parser):
    lvm_options = parser.add_argument_group("LVM Options")
    lvm_options.add_argument('--logical-volume',
                           metavar='lvname',
                           default=None,
                           help='The name for the logical volume to be '
                                'backed up. (default: autodetect)'
                          )
    lvm_options.add_argument('--snapshot-name',
                           metavar='snapshot',
                           default=None,
                           help='The name for the new logical volume '
                                'snapshot. (default: target volume + '
                                '_snapshot)'
                          )
    lvm_options.add_argument('--snapshot-size',
                           metavar='size',
                           default=None,
                           help='Gives  the  size to allocate for the new '
                                'logical volume. (default: the smaller of 20%% '
                                'of --logical-volume size or the free space on'
                                ' the underlying volume group)'
                          )
    lvm_options.add_argument('--mount-directory',
                           metavar='mount-directory',
                           default='/mnt/snapshot',
                           help="Where to mount the snapshot "
                                "(default: %(default)s)")
    parser.add_argument_group(lvm_options)

def _build_mysql_options(parser):
    # MySQL Connection Options
    mysql_options = parser.add_argument_group("MySQL Connection Options",
                                         "These options configure how "
                                         "pylvmbackup connects to MySQL "
                                         "in order to perform any necessary "
                                         "flush or administrative actions.")
    mysql_options.add_argument('--defaults-file',
                             metavar='option-file',
                             default='~/.my.cnf',
                             help="MySQL .cnf file to use (default: %(default)s)")
    mysql_options.add_argument('-u', '--user',
                             metavar='user',
                             default=pwd.getpwuid(os.geteuid()).pw_name,
                             help='MySQL User (default: %(default)s)')
    mysql_options.add_argument('-p', '--password', action='store_true',
                             default=False,
                             help='Prompt for MySQL password. '
                                  'Note: This option takes no argument. '
                                  'Setting a password on the command line '
                                  'is bad practice - use a --defaults-file '
                                  'instead. (default: %(default)s)')
    mysql_options.add_argument('-h', '--host', metavar='host',
                             default='localhost',
                             help='Host of MySQL Server. (default: %(default)s)')
    mysql_options.add_argument('-S', '--socket', metavar='socket-file',
                             default=None,
                             help='Socket file of MySQL server. '
                                  '(default: %(default)s)')
    mysql_options.add_argument('-P', '--port', type='int', metavar='port',
                             default=3306,
                             help='MySQL port number. (default: %(default)s)')
    mysql_options.add_argument('--skip-extra-flush-tables',
                               action='store_false',
                               dest='extra_flush_tables',
                               default=True, # <- extra_flush_tables is set
                               help='Don\'t Run an extra FLUSH TABLES before '
                                    'acquiring a global read lock with FLUSH '
                                    'TABLES WITH READ LOCK (default: no)'
                              )
    mysql_options.add_argument('--skip-flush-tables',
                             action='store_false',
                             dest='flush_tables',
                             default=True, # <- flush_tables defaults to true
                             help="Don't flush tables or acquire a read-lock."
                                  "(default: %(default)s)"
                            )
    mysql_options.add_argument('--innodb-recovery',
                             action='store_true',
                             default=False,
                             help='Run a MySQL bootstrap process against the '
                                  'LV snapshot to initiate InnoDB recovery prior '
                                  'to making the backup. (default: %(default)s)'
                            )
    parser.add_argument_group(mysql_options)

def build_option_parser():
    parser = MyArgumentParser(add_help=False)
    parser.add_argument('--help', action='help',
                            help='Show help.')
    parser.add_argument('-c', '--config',
                         action='store',
                         metavar='config-file',
                         default='/etc/pylvmbackup.conf',
                         help='Use the specified config file '
                              '(default: %(default)s)')
    parser.add_argument('-l', '--log-level',
                         default='info',
                         choices=['debug','info','warning','error','critical'],
                         help="Set log verbosity level. (default: %(default)s)")
    parser.add_argument('backup_file', nargs=1, type=argparse.FileType('w'),
                        help="Destination file to store tar archive")
    _build_lvm_options(parser)
    _build_mysql_options(parser)

    return parser

if __name__ == '__main__':
    p = build_option_parser()
    opts = p.parse_args(namespace=DictNamespace({}))
    print opts
