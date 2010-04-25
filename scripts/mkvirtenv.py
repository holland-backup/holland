#!/usr/bin/env python

"""Setup a python virtual environment to test holland"""

import sys, os
import signal
import shutil
import logging
import subprocess
from optparse import OptionParser
from os.path import abspath, join, dirname, basename, expanduser
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
    env['PS1'] = r'[holland-test]% '
    env['PROMPT'] = env['PS1']
    env['HOLLAND_CONFIG'] = join(virtual_env_root,
                                 'etc',
                                 'holland',
                                 'holland.conf')
    return env

def start_shell(virtual_env):
    """Start a shell in the virtual environment"""
    shell = os.environ.get('SHELL', '/bin/bash')
    logging.info("Starting shell in virtual environment %s - "
                 "use ctrl-d to exit", shell)
    args = [shell]
    if basename(shell) == 'zsh':
        args += ['--no-globalrcs']
    pid = subprocess.Popen(args, env=virtual_env)
    while True:
        try:
            if pid.wait() is not None:
                logging.info("Shell exited with status %d", pid.returncode)
                break
        except KeyboardInterrupt:
            logging.info("start_shell SIGTERM")
            pass
    return pid.returncode

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
    holland_core = join(HOLLAND_ROOT)
    ret = run_setup_develop(cwd=holland_core, env=env)
    if ret != 0:
        logging.error("Failed to install holland-core")
    else:
        logging.info("Installed holland-core.")

def install_plugins(virtual_env, egg_env):
    """Install (active) holland plugins"""
    logging.info("Installing holland plugins")
    for plugin_dir in open(join(HOLLAND_ROOT, 'plugins', 'ACTIVE')):
        plugin_dir = plugin_dir.rstrip()
        if plugin_dir in egg_env:
            logging.info("%r found in test environment. Not installing.", 
                         plugin_dir)
            continue
        plugin_path = join(HOLLAND_ROOT, 'plugins', plugin_dir)
        ret = run_setup_develop(cwd=plugin_path, env=virtual_env)
        if ret != 0:
            logging.error("Failed to install plugin %s", plugin_dir)
        else:
            logging.info("Installed plugin %s", plugin_dir)

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

    if os.path.exists(holland_etc):
        logging.info("An existing config already exists in %s. Not installing test configs.",
                        holland_etc)
        return
    # copytree doesn't create all dirs on python 2.4
    if not os.path.exists(join(env_root, 'etc')):
        os.makedirs(join(env_root, 'etc'))
    shutil.copytree(join(HOLLAND_ROOT, 'test_config'),
                    join(env_root, 'etc', 'holland'))

def find_egg_env(path):
    from pkg_resources import Environment
    return Environment([path])

def main(args=None):
    """Main script entry point"""
    oparser = OptionParser()
    oparser.add_option('--distribute', action='store_true',
                       default=False,
                       help='Use Distribute instead of Setuptools')
    oparser.add_option('--clear', action='store_true',
                       default=False,
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
    egg_env = find_egg_env(os.path.join(home_dir, 'lib', 'python2.4', 'site-packages'))
    if 'holland' in egg_env:
        logging.info("'holland' found in environment. Not reinstalling.")
    else:
        install_holland(virtualenv)
    install_plugins(virtualenv, egg_env)

    install_configs(home_dir)
    result = start_shell(virtualenv)
    logging.info("Exiting virtual environment[%d]", result)
    return result

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logging.warn("Interrupted")
        sys.exit(1)
