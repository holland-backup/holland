#!/usr/bin/env python

import sys, os
import shutil
import re
import tarfile
from subprocess import Popen, PIPE 
from optparse import OptionParser, IndentedHelpFormatter

VERSION='0.2'

config = {}
config['srcdir'] = os.getcwd()
config['topdir'] = os.path.join(os.environ['HOME'], 'holland-buildroot')
config['spec'] = './contrib/holland.spec'

def get_opts_args():
    fmt = IndentedHelpFormatter(
            indent_increment=4, max_help_position=32, width=77, short_first=1
            )
    parser = OptionParser(formatter=fmt, version=VERSION)
    parser.usage = """ devtools/build_rpms.py --(OPTIONS)"""

    parser.add_option('--topdir', action='store', dest='topdir',
                      help="tmp directory to build in.")
    parser.add_option('--just-source', action='store', dest='just_source',
                      help="just build the source rpm")
    parser.add_option('--clean', action='store_true', dest='clean',
                      help="remove directory after building (for testing)")
    parser.add_option('--with-plugin', action='append', dest='with_plugins', 
                      default=[], metavar='PLUGIN',
                      help="Include additional plugins not built by default")
    (cli_opts, cli_args) = parser.parse_args()
    return (cli_opts, cli_args)

def prep_buildroot():
    version, dev_tag = get_holland_version()
    dirs = ['RPMS', 'SRPMS', 'BUILD', 'SPECS', 'SOURCES']
    for d in dirs:
        path = os.path.join(config['topdir'], d)
        if not os.path.exists(path):
            os.makedirs(path)
    f = open(config['spec'], 'r')
    data = f.read()
    f.close()
    
    data = re.sub('@@@VERSION@@@', version, data)

    f = open(os.path.join(config['topdir'], 'SPECS', 'holland.spec'), 'w')
    f.write(data)
    f.close()
 
    cmd = "git archive --prefix=holland-%s/ HEAD > %s/SOURCES/holland-%s.tar.gz" % \
                (version, config['topdir'], version)
    print cmd
    os.system(cmd)


def build_srpm():
    version, dev_tag = get_holland_version()
    if dev_tag:
        dev_option = "--define='src_dev_tag dev'"
    else:
        dev_option = ''

    cmd = "rpmbuild -bs %s/SPECS/holland.spec --define='_topdir %s' %s" % \
           (config['topdir'], config['topdir'], dev_option)
    retcode = os.system(cmd)
    return retcode
        
def build_rpms(with_extra):
    version, dev_tag = get_holland_version()
    if dev_tag:
        dev_option = "--define='src_dev_tag dev'"
    else:
        dev_option = ''

    with_extra = ' '.join(['--with %s' % extra for extra in with_extra])
    cmd = "rpmbuild -bb %s/SPECS/holland.spec --define='_topdir %s' %s %s" % \
           (config['topdir'], config['topdir'], dev_option, with_extra)
    print cmd
    retcode = os.system(cmd)
    return retcode


def get_holland_version():
    version = None
    dev_tag = None
    version = Popen(['python', 'setup.py', '--version'], stdout=PIPE, cwd=
                    os.path.join(config['srcdir']))\
                    .communicate()[0].strip('\n')
    try:
        if int(version.split('.')[-1])%2 != 0:
            dev_tag = 'dev'
    except ValueError:
        dev_tag = None

    if not version:
        raise Exception, "unable to determine holland version"
    return version, dev_tag
 
    
def exit(code=0, clean=False):
    if clean:
        if os.path.exists(config['topdir']):
            print "cleaning %s" % config['topdir']
            shutil.rmtree(config['topdir'])
    sys.exit(code)
    
def main():
    (cli_opts, cli_args) = get_opts_args()
    (version, dev_tag) = get_holland_version()
    
    if cli_opts.topdir:
        if not os.path.exists(os.path.abspath(cli_opts.topdir)):
            os.makedirs(os.path.abspath(cli_opts.topdir))
        config['topdir'] = os.path.abspath(cli_opts.topdir) 
        
    prep_buildroot()
    retcode = build_srpm()
    if int(retcode) != 0:
        print
        print '-' * 77
        print
        print "Please correct the above errors"
        print
        exit(1, cli_opts.clean)

    if not cli_opts.just_source:
        retcode = build_rpms(cli_opts.with_plugins)

    print
    print '-' * 77
    print 

    if int(retcode) == 0:
        print "Holland %s%s built in %s" % (version, dev_tag, config['topdir'])
        exit(0, cli_opts.clean)
    else:     
        print "Holland %s%s build FAILED!  Files in %s" % (version, dev_tag, 
                                                           config['topdir'])
        exit(1, cli_opts.clean)
    print
    
if __name__ == '__main__':
    main()
