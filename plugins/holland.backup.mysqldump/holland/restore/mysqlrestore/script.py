"""Main mysqlrestore script method"""

import os
import sys
import math
import time
import select
import logging
import argparse

from mysqldump.parser import Parser
from mysqldump.filter import SchemaFilter

class DbRewriter(object):
    def __init__(self, name_map):
        self.name_map = name_map

    def __call__(self, name):
        return self.name_map.get(name, name)

  
def format_bytes(bytes, precision=2):
    """Format an integer number of bytes to a human readable string."""

    if bytes < 0:
        raise ArithmeticError("Only Positive Integers Allowed")

    if bytes != 0:
        exponent = math.floor(math.log(bytes, 1024))
    else:
        exponent = 0

    return "%.*f%s" % (
        precision,
        bytes / (1024 ** exponent),
        ['B','KB','MB','GB','TB','PB','EB','ZB','YB'][int(exponent)]
    )
 
def terminal_width():
    """Return estimated terminal width."""
    width = 0
    try:
        import struct, fcntl, termios
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(2, termios.TIOCGWINSZ, s)
        width = struct.unpack('HHHH', x)[1]
    except IOError:
        pass
    if width <= 0:
        try:
            width = int(os.environ['COLUMNS'])
        except:
            pass
    if width <= 0:
        width = 80

    return width

class Progress(object):
    def __init__(self, parser):
        self.parser = parser
        self.total_bytes = 0
        self.last = time.time()
        self.start = time.time()

    def __call__(self, n):
        self.total_bytes += n
        tbl = '.'.join((str(self.parser.current_db), str(self.parser.current_tbl)))
        self.last = time.time()
        rate = self.total_bytes / (self.last - self.start)
        output = "Table: %s Transferred: %s Elapsed: %.2fs Rate: %s per second" % (tbl, format_bytes(self.total_bytes), (self.last - self.start), format_bytes(rate))
        pad = " "*(terminal_width() - len(output))
        print >>sys.stderr, "%s%s\r" % (output, pad),

def run(options):
    input = options.sql_file

    if input == '-':
       input = sys.stdin

    rewrite_map = dict()

    logging.info("options.destination = %r", options.destination)
    for name in options.destination:
        if '=' not in name:
            rewrite_map[name] = name
            rewrite_map.setdefault(None, name)
        else:
            src, dst = name.split('=', 1)
            rewrite_map[src] = dst
            rewrite_map.setdefault(None, src)

    logging.info("rewrite_map = %r", rewrite_map)
    filter = SchemaFilter(options.databases,
                          options.exclude_databases,
                          options.tables,
                          options.exclude_tables)

    parser = Parser(input,
                    schema_filter=filter, 
                    binlog=options.binlog, 
                    replication=options.replication, 
                    dbrewriter=DbRewriter(rewrite_map))


    progress = options.show_progress and Progress(parser) or (lambda x: x)

    for line in parser:
        while line:
            result = select.select([], [1], [], 1.0)
            if result[1]: # <- wfds populated
                n = os.write(1, line)
                line = line[n:]
            progress(n)
    progress(0)
    print >>sys.stderr



def start(args=None):
    logging.basicConfig(level=logging.ERROR)
    logging.info("sys.argv = %r", sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('--sql-file', default="-",
                        help="SQL file to restore. Default stdin.")
    parser.add_argument('--databases', nargs='+',
                        default=['*'],
                        metavar="db",
                        help="Databases to extract")
    parser.add_argument('--exclude-databases', nargs='+',
                        default=[],
                        metavar="db",
                        help="Databases to exclude")
    parser.add_argument('--tables', nargs=1,
                        default=['*'],
                        metavar="tbl|db.tbl",
                        help="Tables to extract.")
    parser.add_argument('--exclude-tables', nargs='+',
                        default=[],
                        metavar="tbl|db.tbl",
                        help="Tables to exclude")
    parser.add_argument('--binary-log',
                        action='store_true',
                        help="Write this restore to the binary log")
    parser.add_argument('--skip-binary-log', action='store_false',
                        dest='binlog',
                        default=True, # default binlog = True
                        help="Append SQL_LOG_BIN=0 to dump file header")
    parser.add_argument('--replication',
                        action='store_true',
                        default=False,
                        help="Uncomment CHANGE MASTER line, if present")
    parser.add_argument('--skip-confirm', action='store_true',
                        default=False,
                        help="Don't confirm the restore actions.")
    parser.add_argument('--show-progress', action='store_true',
                        default=False,
                        help="Display a progress meter")
    parser.add_argument("--mysql-client",
                        default="mysql",
                        metavar='path',
                        help="Set a specific path for the mysql client - "
                             "slaved for the restore. (default: %(default)s)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--schema-only', action='store_true')
    group.add_argument('--data-only', action='store_true')
    parser.add_argument('destination', nargs='*',
                        help="Where to restore to.  Either a database name or \
                              a src[.tbl]=dst[.tbl] rewrite rule.  If \
                              multiple destinations are specified, these must \
                              be rewrite rules (src=dst)")
    options = parser.parse_args(args)
    try:
        return run(options)
    except SyntaxError, e:
        print >>sys.stderr, "Error parsing input: %s" % (e)
    except KeyboardInterrupt:
        print >>sys.stderr, "Interrupted"
        return 1

if __name__ == '__main__':
    sys.exit(start())
