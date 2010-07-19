#!/usr/bin/env python
import sys
import shlex
import logging
import commands
from tarfile import TarFile
from optparse import OptionParser

def main(args=None):
    parser = OptionParser()
    parser.add_option('--version', default=None)
    opts, args = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO,
                        format='[%(levelname)s] %(message)s')

    if not opts.version:
        version = commands.getoutput('python setup.py --version')
    else:
        version = opts.version

    name = 'holland-%s' % version

    status, output = commands.getstatusoutput('git archive --prefix=%s/ HEAD '
                                              '| gzip --fast > %s.tar.gz' %
                                              (name, name))
    if status != 0:
        logging.error("%s failed.", sys.argv[0])
        return 1
    else:
        logging.info("created archive %s.tar.gz", name)
        return 0


if __name__ == '__main__':
    sys.exit(main())
