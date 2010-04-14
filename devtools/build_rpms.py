#!/usr/bin/env python

import sys, os
import shutil
import re
import tarfile
from subprocess import Popen, PIPE 
from tempfile import mkdtemp
from optparse import OptionParser, IndentedHelpFormatter

VERSION='0.1'

config = {}
config['srcdir'] = os.getcwd()
config['topdir'] = mkdtemp(prefix="%s/" % os.environ['HOME'])
config['spec'] = './distribution/holland.spec'

def get_opts_args():
    fmt = IndentedHelpFormatter(
            indent_increment=4, max_help_position=32, width=77, short_first=1
            )
    parser = OptionParser(formatter=fmt, version=VERSION)
    parser.usage = """ devtools/build_rpms.py --(OPTIONS)"""

    parser.add_option('--tmpdir', action='store', dest='tmpdir',
                      help="tmp directory to build in.")
    parser.add_option('--just-source', action='store', dest='just_source',
                      help="just build the source rpm")
    parser.add_option('--clean', action='store_true', dest='clean',
                      help="remove directory after building (for testing)")
    (cli_opts, cli_args) = parser.parse_args()
    return (cli_opts, cli_args)

def prep_buildroot():
    version, dev_tag = get_holland_version()
    if os.path.exists(config['topdir']):
        shutil.rmtree(config['topdir'])
    dest_srcdir = os.path.join(config['topdir'], 'SOURCES', 'holland-%s' % version)    
    dirs = ['RPMS', 'SRPMS', 'BUILD', 'SPECS', 'SOURCES']
    for d in dirs:
        os.makedirs(os.path.join(config['topdir'], d))
    
    f = open(config['spec'], 'r')
    data = f.read()
    f.close()
    
    data = re.sub('@@@VERSION@@@', version, data)

    f = open(os.path.join(config['topdir'], 'SPECS', 'holland.spec'), 'w')
    f.write(data)
    f.close()
 
    shutil.copytree(config['srcdir'], dest_srcdir)
    os.chdir(os.path.join(config['topdir'], 'SOURCES'))
    t = tarfile.open('%s.tar.gz' % dest_srcdir, 'w:gz')
    t.add(os.path.basename(dest_srcdir))
    t.close()


def build_srpm():
    version, dev_tag = get_holland_version()
    if dev_tag:
        dev_option = "--define='src_dev_tag dev'"
    else:
        dev_option = ''

    os.chdir(config['topdir'])
    cmd = "rpmbuild -bs %s/SPECS/holland.spec --define='_topdir %s' %s" % \
           (config['topdir'], config['topdir'], dev_option)
    retcode = os.system(cmd)
    return retcode
        
def build_rpms():
    version, dev_tag = get_holland_version()
    if dev_tag:
        dev_option = "--define='src_dev_tag dev'"
    else:
        dev_option = ''

    os.chdir(config['topdir'])
    cmd = "rpmbuild -bb %s/SPECS/holland.spec --define='_topdir %s' %s" % \
           (config['topdir'], config['topdir'], dev_option)
    retcode = os.system(cmd)
    return retcode


def get_holland_version():
    version = None
    dev_tag = None
    version = Popen(['python', 'setup.py', '--version'], stdout=PIPE, cwd=
                    os.path.join(config['srcdir'], 'holland-core'))\
                    .communicate()[0].strip('\n')
    if int(version.split('.')[2])%2 != 0:
        dev_tag = 'dev'
    if not version:
        raise Exception, "unable to determine holland version"
    return version, dev_tag
 
    
def exit(code=0, clean=False):
    if clean:
        if os.path.exists(cli_opts.tmpdir):
            print "cleaning %s" % config['topdir']
            shutil.rmtree(config['topdir'])
    sys.exit(code)
    
def main():
    (cli_opts, cli_args) = get_opts_args()
    (version, dev_tag) = get_holland_version()
    
    if cli_opts.tmpdir:
        if not os.path.exists(cli_opts.tmpdir):
            os.makedirs(cli_opts.tmpdir)
        config['topdir'] = mkdtemp(prefix="%s/" % cli_opts.tmpdir)
        
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
        retcode = build_rpms()

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
