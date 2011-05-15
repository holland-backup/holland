"""Test the stream interfaces"""

import os, sys
from nose.tools import *
from holland.core.stream import *


def test_available_methods():
    ok_('builtin' in available_methods())

def test_open_stream():
    obj = open_stream(__file__, 'r', method='builtin')
    assert_equals(obj.__class__, file)

def test_missing_method():
    assert_raises(IOError, open_stream, 'foo', 'r', method='baz')

def test_default_method():
    obj = open_stream(__file__, 'r')
    assert_equals(obj.__class__, file)

def test_stream_info():
    info = load_stream_plugin('builtin').stream_info('foo', 'r')

    ok_(isinstance(info, dict))
    assert_equals(info['extension'], '')

def test_open_stream_wrapper():
    wrapper = open_stream_wrapper(os.path.dirname(__file__), method='builtin')
    wrapper(os.path.basename(__file__), 'r')
