"""Test helper for running holland unit tests."""

import os
import sys
import glob
import shutil
import tempfile
import logging
from distutils.sysconfig import get_python_lib
from optparse import OptionParser
from subprocess import call, Popen, PIPE, STDOUT, list2cmdline

PREFIX = os.environ.get('HOLLAND_HOME', '/usr')
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def exec_command(argv, *args, **kwargs):
    """
    Quick wrapper around subprocess to exec shell command.

    Required Arguments:

        cmd_args
            The args to pass to subprocess.

    """
    if isinstance(argv, basestring):
        logging.info("+ /bin/sh -c '%s'", argv)
    else:
        logging.info("+ %s", list2cmdline(argv))

    proc = Popen(argv, *args, **kwargs)
    (stdout, stderr) = proc.communicate()
    ret = proc.wait()
    return (ret, stdout, stderr)

class TestRunner(object):
    def __init__(self,
                 python='python',
                 pylint='pylint',
                 coverage='coverage',
                 report=False,
                 quiet=True):
        self.python = python
        self.pylint = pylint
        self.coverage = coverage
        self.report = report
        self.quiet = quiet

    def _setup_python_path(self, paths):
        python_path = []
        for path in paths:
            logging.info("Check %s", path)
            if os.path.isdir(path):
                python_path.append(path)
                exec_command('python setup.py egg_info',
                             stdout=open('/dev/null', 'w'),
                             stderr=open('/dev/null', 'w'),
                             shell=True,
                             cwd=path)
        os.environ['PYTHONPATH'] = ':'.join(python_path)

        return True

    def _check_paths(self):
        ok = True

        for name in (self.python, self.pylint, self.coverage):
            try:
                exec_command([name, '--help'],
                             stdout=open('/dev/null', 'w'),
                             stderr=STDOUT,
                             close_fds=True)
            except OSError, exc:
                logging.error("%s is not runnable: %s", name, exc)
                break
        else:
            return True

        return False

    def _run_tests(self, paths):
        args = [
            self.python,
            'setup.py',
            'nosetests',
            '--verbosity=3',
        ]

        if self.report:
            args.extend([
                '--with-coverage',
                '--cover-erase',
                '--with-xunit',
                '--cover-tests',
            ])

        for path in paths:
            logging.info("Testing: %s", path)
            ret, stdout, stderr = exec_command(args,
                                               #stdout=open('/dev/null', 'w'),
                                               stderr=STDOUT,
                                               cwd=path,
                                               close_fds=True)
            if ret != 0:
                logging.warning(" * Test exited with failure status %d", ret)

            if self.report:
                exec_command(['coverage', 'xml',
                              '--omit',
                              'tests,holland/cli/backports,/usr/,/var/'],
                             cwd=path,
                             close_fds=True)

        return True

    def _run_pylint(self, paths):
        logging.info("Running PyLint across project...")
        args = [
            self.pylint,
            '-f',
            'parseable',
            'holland',
        ]
        staging = tempfile.mkdtemp()

        try:
            stage_args = [
                'python',
                'setup.py',
                'install',
                '--root=' + staging,
                '--single-version-externally-managed',
            ]
            if os.path.exists('/etc/debian_version'):
                stage_args.append('--install-layout=deb')
            for path in paths:
                logging.info(" * Installing from %s", path)
                exec_command(stage_args,
                             stdout=open('/dev/null', 'w'),
                             stderr=STDOUT,
                             cwd=path,
                             close_fds=True)

            os.environ['PYLINTRC'] = os.path.join(SRC_ROOT,
                                                  os.path.abspath('.pylintrc'))
            logging.info("Running pylint relative to %s",
                         os.path.join(staging, get_python_lib()[1:]))
            exec_command([self.pylint, '-f', 'parseable', 'holland'],
                         stdout=open(os.path.join(SRC_ROOT, 'pylint.txt'), 'w'),
                         cwd=os.path.join(staging,
                                          get_python_lib()[1:]),
                         close_fds=True)
        finally:
            shutil.rmtree(staging)

    def run(self, paths):
        if not self._check_paths():
            raise OSError("Unable to continue.  See errors above.")
        if not self._setup_python_path(paths):
            raise OSError("Unable to continue.  See errors above.")
        if not self._run_tests(paths):
            raise OSError("Unable to continue.  See errors above.")
        self._run_pylint(paths)

def _find_coverage():
    for name in ('coverage', 'python-coverage'):
        try:
            call([name, '--help'],
                 stdout=open('/dev/null', 'w'),
                 stderr=STDOUT,
                 close_fds=True)
            return name
        except OSError:
            continue
    else:
        return 'coverage'

def main(args=None):
    """Main script entry point"""

    oparser = OptionParser()
    oparser.add_option('--report', action='store_true',
                       default=False,
                       help='create report data')
    oparser.add_option('--quiet', action='store_true',
                       default=False,
                       help='limit output')
    oparser.add_option('--python', default='python')
    oparser.add_option('--pylint', default='pylint')
    oparser.add_option('--coverage', default=_find_coverage())
    oparser.add_option('--include', action='append', dest='include',
                       metavar="PATH", help='directories to include in tests')
    oparser.add_option('--debug', action='store_true')
    opts, args = oparser.parse_args(args)

    logging.basicConfig(level=opts.debug and logging.DEBUG or logging.INFO,
                        format='[%(levelname)s] %(message)s')

    # list of directories to test in
    if opts.include and len(opts.include) > 0:
        paths = []
        for path in opts.include:
            paths.append(os.path.abspath(path))
    else:
        paths = [
                os.path.abspath(path)
                for path in [SRC_ROOT] + glob.glob('plugins/*')
                if os.path.isdir(path)
        ]

    runner = TestRunner(python=opts.python,
                        pylint=opts.pylint,
                        coverage=opts.coverage,
                        report=opts.report,
                        quiet=opts.quiet)
    runner.run(paths)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
