# pylint: skip-file

import os
from holland.backup.lvm.util import *
from nose.tools import *

def test_format_bytes():
    ok_(format_bytes(1024,0) == '1KB')
    ok_(format_bytes(0) == '0.00Bytes')

def test_relpath():
    ok_(relpath('/tmp/mysql/data', '/tmp/mysql') == 'data')
    ok_(relpath('/tmp/mysql', '/tmp/mysql') == '.')
    assert_raises(ValueError, relpath, None)

def test_getdevice():
    assert_equal(getdevice('/tmp'),
                 os.getenv('TMPDEV', ''),
                 msg="getdevice(/tmp) = %r but expected %r" % \
                    (getdevice('/tmp'), os.getenv('TMPDEV'))
                )
    ok_(getdevice('/NoSuchDirectory') is None)

def test_getmount():
    ok_(getmount('/tmp/mysql') == getmount('/tmp'))
    ok_(getmount('/') == '/')
