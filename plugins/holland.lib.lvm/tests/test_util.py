# pylint: skip-file

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
    # XXX: bad hack
    dev = open('/etc/mtab', 'r').readline().split()[0].strip()
    assert_equals(getdevice('/'), dev)
    assert_equals(getdevice('/foobarbaz'), None)

def test_relpath():
    assert_raises(ValueError, relpath, '')
    assert_equals(relpath('/foo/bar/baz', '/foo/bar'), 'baz')
    assert_equals(relpath('/foo/bar/', '/foo/bar/'), os.curdir)
    assert_equals(relpath('/var/lib/mysql', '/'), 'var/lib/mysql')

def test_signalmanager():
    sigmgr = SignalManager()
    sigmgr.trap(signal.SIGINT)
    os.kill(os.getpid(), signal.SIGINT)
    ok_(sigmgr.pending)
    assert_equals(sigmgr.pending[0], signal.SIGINT)
    sigmgr.restore()
    assert_raises(KeyboardInterrupt, os.kill, os.getpid(), signal.SIGINT)

def test_parsebytes():
    # bytes without units should be interpretted as MB
    bytes = parse_bytes('1024')
    assert_equals(bytes, 1024**3)
    # this should not be bytes
    ok_(bytes > 1024)

    bytes = parse_bytes('1024G')
    assert_equals(bytes, 1024**4)
