# pylint: skip-file

from nose.tools import *
from holland.backup.lvm.pylvm.api import run_cmd, which, LVMError

def test_fail_cmd():
    assert_raises(LVMError, run_cmd, '/bin/false')

def test_lvm_warning_cmd():
    assert_raises(EnvironmentError, run_cmd, 'python', '-c', 'import sys; print >>sys.stderr, "WARNING: TEST"')

def test_which_notfound():
    assert_raises(LVMError, which, '/bin/foo_bar_baz_9876543210')
