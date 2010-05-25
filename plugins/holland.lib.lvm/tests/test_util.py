import os
import signal
from nose.tools import *
from holland.lib.lvm.util import *

def test_format_bytes():
    assert_equals(format_bytes(1024), '1.00KB')
    assert_equals(format_bytes(0), '0.00Bytes')

def test_getmount():
    assert_equals(getmount('/'), '/')
    assert_equals(getmount('/foobarbaz'), '/')

def test_getdevice():
    assert_equals(getdevice('/'), '/dev/root')
    assert_equals(getdevice('/foobarbaz'), None)

def test_relpath():
    assert_raises(ValueError, relpath, '')
    assert_equals(relpath('/foo/bar/baz', '/foo/bar'), 'baz')
    assert_equals(relpath('/foo/bar/', '/foo/bar/'), os.curdir)

def test_signalmanager():
    sigmgr = SignalManager()
    sigmgr.trap(signal.SIGINT)
    os.kill(os.getpid(), signal.SIGINT)
    ok_(sigmgr.pending)
    assert_equals(sigmgr.pending[0], signal.SIGINT)
    sigmgr.restore()
    assert_raises(KeyboardInterrupt, os.kill, os.getpid(), signal.SIGINT)
