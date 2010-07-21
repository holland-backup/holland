#!/usr/bin/env python

import sys, os
import time
import shutil
import logging
import subprocess
from os.path import join, dirname, abspath

config = {}
config['srcdir'] = abspath(join(dirname(__file__), '..'))
config['debian'] = join(config['srcdir'], 'contrib', 'debian')

def holland_version():
    holland_core_dir = join(config['srcdir'])
    args = ['python', 'setup.py', '--version']
    return subprocess.Popen(args, stdout=subprocess.PIPE, cwd=holland_core_dir).communicate()[0].strip()

def changelog_time():
    time_str = time.strftime('%a, %d %b %Y %H:%M:%S ')
    offset = ('-','+')[time.altzone > 0]
    offset += '%04d' % time.altzone
    return time_str + offset

def update_changelog():
    format = """\
holland (%(version)s-local-%(today)s) unstable; urgency=low

  * Non-maintainer upload

 -- %(name)s <%(email)s>  %(date)s
"""
    version = holland_version()
    entry = format % { 'version' : version,
                       'name' : 'Unknown',
                       'email': 'example@foo.com',
                       'today': time.strftime('%Y%M%d%H%M'),
                       'date' : changelog_time()
                     }
    src = join(config['debian'], 'changelog')
    changelog = open(src + '.new', 'w')
    print >>changelog, entry,
    shutil.copyfileobj(open(src), changelog)
    changelog.close()
    os.rename(src + '.new', src)
    logging.info("Updated %s with NMU changelog", src)
                        
def check_prereq():
    control_file = join(config['debian'], 'control')
    assert os.path.exists('/usr/bin/dpkg-checkbuilddeps'), \
        "dpkg-dev required to build the Holland debian packages"
    assert os.path.exists('/usr/bin/debuild'), \
        "devscripts required to build the Holland debian packages"

    args = ['dpkg-checkbuilddeps', control_file]
    logging.info("Checking prereqs. Running %s", subprocess.list2cmdline(args))
    ret = subprocess.call(args)
    return ret

def prep_tree():
    src = config['debian']
    dst = join(config['srcdir'], 'debian')
    
    if os.path.exists(dst):
        if os.path.islink(dst):
            os.unlink(dst)
        else:
            shutil.rmtree(dst)
 
    shutil.copytree(src, dst)
    logging.info("Copied %s to %s", src, dst)
    update_changelog()

def build_deb():
    args = [
        'debuild',
        '--no-tgz-check',
        '-rfakeroot',
        '-us',
        '-uc',
    ]
    logging.info("Running %s", subprocess.list2cmdline(args))
    return subprocess.call(args)

def cleanup_tree():
    args = [
        'debuild',
        'clean'
    ]
    logging.info("Running %s", subprocess.list2cmdline(args))
    subprocess.call(args)
    src = config['debian']
    dst = join(config['srcdir'], 'debian')
    if os.path.samefile(src, dst):
        os.unlink(dst)
        logging.info("Unlinked %s", dst)

def config_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    config_logging()
    if check_prereq() != 0:
        return 1
    try:
        try:
            prep_tree()
            return build_deb()
        except AssertionError, exc:
            logging.fatal("%s", exc)
            return 1
    finally:
        cleanup_tree()
    
if __name__ == '__main__':
    sys.exit(main())
