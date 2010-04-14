#!/usr/bin/env python

import sys, os
import shutil
import re
import tarfile
from subprocess import Popen, PIPE 
from tempfile import mkdtemp

config = {}
config['srcdir'] = os.getcwd()
config['topdir'] = mkdtemp(prefix="%s/" % os.environ['HOME'])
config['spec'] = './distribution/holland.spec'


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
        
def build_rpms(just_source=False):
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
 
    
def main():
    just_source = False
    try:
        if sys.argv[1] == '--just-source':
            just_source = True
    except IndexError, e:
        pass

    prep_buildroot()
    retcode = build_srpm()
    if int(retcode) != 0:
        print
        print '-' * 77
        print
        print "Please correct the above errors"
        print
        sys.exit()

    if not just_source:
        retcode = build_rpms(just_source)

    if int(retcode) == 0:
        print
        print '-' * 77
        print 
        print "Holland %s built in %s" % (get_holland_version()[0], config['topdir'])
        print
    else:     
        print
        print '-' * 77
        print 
        print "Holland %s build FAILED!  Files in " % get_holland_version()[0]
        print
    
if __name__ == '__main__':
    main()
