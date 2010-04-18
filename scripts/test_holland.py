#!/usr/bin/env python

"""Setup a python virtual environment to test holland"""

import sys, os
import signal
import shutil
import logging
import subprocess
from optparse import OptionParser
from os.path import abspath, join, dirname, basename, expanduser
from ConfigParser import RawConfigParser
try:
    import curses
    curses.setupterm()
except ImportError:
    curses = None

from _virtualenv import create_environment

HOLLAND_ROOT = abspath(join(dirname(__file__), '..'))

def make_env(virtual_env_root):
    """Setup an environment dictionary suitable for passing to
    ``subprocess.Popen`` that allows commands to run correctly
    in the virtual environment specified by ``virtual_env_root``
    """
    env = dict(os.environ) # copy environment
    env['VIRTUAL_ENV'] = virtual_env_root
    env['PATH'] = ':'.join(
                            [
                                join(virtual_env_root, 'bin'),
                                os.environ.get('PATH', ''),
                            ]
                        )
    env['PS1'] = r'[\e[31;1mholland:%s\e[0m]%s ' % (basename(virtual_env_root),
                             os.environ.get('PS1', '#'))
    env['PROMPT'] = env['PS1']
    env['HOLLAND_CONFIG'] = join(virtual_env_root,
                                 'etc',
                                 'holland',
                                 'holland.conf')
    return env

def install_testutils(virtual_env):
    """Install useful testing packages into virtual environment"""
    subprocess.call(['easy_install', 'nose'], env=virtual_env)
    subprocess.call(['easy_install', 'coverage'], env=virtual_env)
    subprocess.call(['easy_install', 'MySQL-python'], env=virtual_env)

def run_tests(virtual_env):
    """Start a shell in the virtual environment"""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    args = [
        'python',
        'setup.py',
        'nosetests',
        '--with-coverage',
        '--with-xunit',
    ]
    subprocess.call(args, cwd=abspath(join(HOLLAND_ROOT, 'holland-core')), env=virtual_env)
    subprocess.call(['coverage', 'xml'], cwd=abspath(join(HOLLAND_ROOT, 'holland-core')), env=virtual_env)
    for plugin_dir in open(join(HOLLAND_ROOT, 'plugins', 'ACTIVE')):
        plugin_dir = plugin_dir.rstrip()
        plugin_path = join(HOLLAND_ROOT, 'plugins', plugin_dir)
        subprocess.call(args, cwd=plugin_path, env=virtual_env)
        subprocess.call(['coverage', 'xml'], cwd=plugin_path, env=virtual_env)
    for addon_dir in open(join(HOLLAND_ROOT, 'addons', 'ACTIVE')):
        addon_dir = addon_dir.rstrip()
        addon_path = join(HOLLAND_ROOT, 'addons', addon_dir)
        subprocess.call(args, cwd=addon_path, env=virtual_env)
        subprocess.call(['coverage', 'xml'], cwd=plugin_path, env=virtual_env)
    #return subprocess.call(args, env=virtual_env)

def run_setup_develop(cwd, env):
    """Run python setup.py --develop in the specified working directory
    and with the provided environment dictionary
    """
    log_path = join(env['VIRTUAL_ENV'], 'holland_install.log')
    return subprocess.call(['python', 'setup.py', 'develop'],
                           stdout=open(log_path, 'a'),
                           stderr=subprocess.STDOUT,
                           cwd=cwd,
                           env=env)

def install_holland(virtual_env):
    """Install holland-core"""
    env = dict(virtual_env)
    holland_core = join(HOLLAND_ROOT, 'holland-core')
    ret = run_setup_develop(cwd=holland_core, env=env)
    if ret != 0:
        logging.error("Failed to install holland-core")
    else:
        logging.info("Installed holland-core.")

def install_plugins(virtual_env):
    """Install (active) holland plugins"""
    logging.info("Installing holland plugins")
    for plugin_dir in open(join(HOLLAND_ROOT, 'plugins', 'ACTIVE')):
        plugin_dir = plugin_dir.rstrip()
        plugin_path = join(HOLLAND_ROOT, 'plugins', plugin_dir)
        ret = run_setup_develop(cwd=plugin_path, env=virtual_env)
        if ret != 0:
            logging.error("Failed to install plugin %s", plugin_dir)
        else:
            logging.info("Installed plugin %s", plugin_dir)

def install_addons(virtual_env):
    """Install (active) Holland addons"""
    logging.info("Installing holland addons")
    for plugin_dir in open(join(HOLLAND_ROOT, 'addons', 'ACTIVE')):
        plugin_dir = plugin_dir.rstrip()
        addon_path = join(HOLLAND_ROOT, 'addons', plugin_dir)
        ret = run_setup_develop(cwd=addon_path, env=virtual_env)
        if ret != 0:
            logging.error("Failed to install addon %s", plugin_dir)
        else:
            logging.info("Installed holland addon %s", plugin_dir)

if curses:
    COLOR_NAMES = "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE"
    COLORS = dict(zip(COLOR_NAMES.split(), xrange(8)))
    RESET = curses.tigetstr('sgr0')
    def colorize(record):
        levelno = record.levelno
        if(levelno>=40):
            color = COLORS['RED'] # red
        elif(levelno>=30):
            color = COLORS['YELLOW'] # yellow
        elif(levelno>=20):
            color = COLORS['GREEN'] # green 
        elif(levelno>=10):
            color = COLORS['MAGENTA'] 
        else:
            color = RESET # normal
        color = curses.tparm(curses.tigetstr('setaf'), color)
        record.levelname = color + record.levelname + RESET
        return record
else:
    colorize = lambda record: record

class ColorFormatter(logging.Formatter):
    def format(self, record):
        return logging.Formatter.format(self, colorize(record))

def setup_logging(debug):
    """Setup basic console logging"""
    root = logging.getLogger()
    root.setLevel(debug and logging.DEBUG or logging.INFO)
    handler = logging.StreamHandler()
    formatter = ColorFormatter(fmt='[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

def install_configs(env_root):
    """Install testing configs into virtual environment"""
    holland_etc = join(env_root, 'etc', 'holland')
    holland_bk_etc = join(env_root, 'etc', 'holland', 'backupsets')
    holland_pv_etc = join(env_root, 'etc', 'holland', 'providers')

    if os.path.exists(join(env_root, 'etc', 'holland')):
        shutil.rmtree(join(env_root, 'etc', 'holland'))
    if not os.path.exists(join(env_root, 'etc')):
	os.mkdir(join(env_root, 'etc'))
    shutil.copytree(join(HOLLAND_ROOT, 'test_config'),
                    join(env_root, 'etc', 'holland'))

    # fixup holland.conf
    cfg = RawConfigParser()
    cfg.read([os.path.join(env_root, 'etc', 'holland', 'holland.conf')])
    cfg.set('holland', 'plugin_dirs', os.path.join(env_root, 'usr', 'share', 'holland', 'plugins'))
    cfg.set('holland', 'backup_directory', os.path.join(env_root, 'var', 'spool', 'holland'))
    cfg.write(open(os.path.join(env_root, 'etc', 'holland', 'holland.conf'), 'w'))

def main(args=None):
    """Main script entry point"""
    oparser = OptionParser()
    oparser.add_option('--distribute', action='store_true',
                       default=False,
                       help='Use Distribute instead of Setuptools')
    oparser.add_option('--clear', action='store_true',
                       default=True,
                       help='Clear out the non-root install and start '
                            'from scratch')
    oparser.add_option('--debug', action='store_true')
    opts, args = oparser.parse_args(args)

    setup_logging(opts.debug)
    home_dir = os.environ.get('HOLLAND_HOME', expanduser('~/holland-test'))
    if home_dir in sys.executable:
        logging.error("Please exit your current virtual environment before trying to create another")
        return 1

    create_environment(home_dir, site_packages=True, clear=opts.clear,
                       unzip_setuptools=False, use_distribute=opts.distribute)
    virtualenv = make_env(home_dir)
    install_holland(virtualenv)
    install_addons(virtualenv)
    install_plugins(virtualenv)
    install_configs(home_dir)
    install_testutils(virtualenv)
    run_tests(virtualenv)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logging.warn("Interrupted")
        sys.exit(1)
