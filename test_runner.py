"""Test helper for running holland unit tests."""

import os
import sys
import logging
from optparse import OptionParser
from subprocess import Popen, PIPE

try:
    if os.isatty(sys.stdout.fileno()):
        import curses
        curses.setupterm()
    else:
        curses = None
except ImportError:
    curses = None
    
PREFIX = os.environ.get('HOLLAND_HOME', '/usr')
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

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

def exec_command(cmd_args):
    """
    Quick wrapper around subprocess to exec shell command.

    Required Arguments:

        cmd_args
            The args to pass to subprocess.

    """
    logging.debug("exec_command: %s" % cmd_args)
    proc = Popen(cmd_args, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = proc.communicate()
    ret = proc.wait()
    return (ret, stdout, stderr)
    
class ColorFormatter(logging.Formatter):
    def format(self, record):
        return logging.Formatter.format(self, colorize(record))
        
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

class TestRunner(object):
    def __init__(self, prefix='/usr', paths=[], report=False, quiet=True):
        self.prefix = prefix
        self.paths = paths
        self.report = report
        self.python_path = None
        self.quiet = quiet
        
        self.python = os.path.join(self.prefix, 'bin', 'python')
        self.pylint = os.path.join(self.prefix, 'bin', 'pylint')
        self.coverage = os.path.join(self.prefix, 'bin', 'coverage')
        
    def _setup_python_path(self):
        python_path = []
        python_path.append('.')
        python_path.append(os.path.join(SRC_ROOT))
        python_path.append(os.path.join(SRC_ROOT, 'plugins', 'holland.lib.common'))
        self.python_path = ':'.join(python_path)
        os.environ['PYTHONPATH'] = self.python_path
        
    def _check_paths(self):
        ok = True
        if not os.path.exists(self.python):
            logging.error("%s does not exist" % self.python)
            ok = False
        for path in self.paths:
            if not os.path.exists(path):
                logging.error("%s does not exist" % path)
                ok = False
        if self.report:
            for path in [self.pylint, self.coverage]:
                if not os.path.exists(path):
                    logging.error("%s does not exist" % path)
                    ok = False
        return ok
        
    def _run_tests(self):
        for path in self.paths:
            logging.info("Testing: %s" % path)
            os.chdir(path)
            if self.report:
                args = [
                    self.python,
                    'setup.py',
                    'nosetests', 
                    '--with-coverage', 
                    '--cover-erase', 
                    '--verbosity=3',
                    '--with-xunit',
                    ]
            else:
                args = [
                    self.python,
                    'setup.py',
                    'nosetests', 
                    '--verbosity=3', 
                    ]
                
            (ret, stdout, stderr) = exec_command(args)
            if ret:
                logging.fatal("FAIL: %s" % path)
                print stderr
            else:
                if not self.quiet:
                    print stderr
                    
            if self.report and os.path.exists('.coverage'):
                dest = os.path.join(SRC_ROOT, 
                                    ".coverage.%s" % os.path.basename(path))
                logging.debug("Adding coverage report %s" % dest)
                os.rename('.coverage', dest)    
                
    def _run_pylint(self):
        logging.info("Running PyLint across project...")
        args = [
            self.pylint,
            '-f', 
            'parseable', 
            'holland', 
            ]
        (ret, stdout, stderr) = exec_command(args)
        if ret:
            logging.warn("PyLint command exited with code '%s'" % ret)
        else:
            f = open(os.path.join(SRC_ROOT, 'pylint.txt'), 'w')
            f.write(stdout)
            f.close()
        
    def _collect_coverage_reports(self):
        logging.info("Combining coverage reports...")
        os.chdir(SRC_ROOT)
        args = [self.coverage, 'combine']
        (ret, stdout, stderr) = exec_command(args)
        if ret:
            print stderr
        else:
            if not self.quiet:
                print stdout
                
    def run(self):
        logging.info("Verifying paths...")
        if not self._check_paths():
            logging.fatal("Unable to continue.  See errors above.")
            sys.exit(1)
        self._setup_python_path()
        self._run_tests()        
        if self.report:
            self._run_pylint()
            self._collect_coverage_reports()
            
        
def main(args=None):
    """Main script entry point"""

    oparser = OptionParser()
    oparser.add_option('--report', action='store_true',
                       default=False,
                       help='create report data')
    oparser.add_option('--quiet', action='store_true',
                       default=False,
                       help='limit output')
    oparser.add_option('--prefix', action='store',
                       default=PREFIX,
                       help='prefix for binary paths')
    oparser.add_option('--include', action='append', dest='include', 
                       metavar="PATH", help='directories to include in tests')
    oparser.add_option('--debug', action='store_true')
    opts, args = oparser.parse_args(args)

    setup_logging(opts.debug)
    
    # list of directories to test in
    if opts.include and len(opts.include) > 0:
        paths = []
        for path in opts.include:
            paths.append(os.path.abspath(path))
    else:
        paths = [
            os.path.join(SRC_ROOT),
            os.path.join(SRC_ROOT, 'plugins', 'holland.backup.random'),
            os.path.join(SRC_ROOT, 'plugins', 'holland.backup.sqlite'),
            ]

    runner = TestRunner(opts.prefix, paths, opts.report, opts.quiet)
    runner.run()
    
if __name__ == '__main__':
    main(sys.argv)