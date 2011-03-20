"""Test the basic config loader/parser"""
import os
import shutil
import tempfile
from textwrap import dedent
from StringIO import StringIO
from nose.tools import *
from holland.core.config import Config

def test_basic():
    data = dedent("""
    [section]
    name = value
    """)

    cfg = Config.from_string(data)
    assert_equals(len(cfg), 1)
    assert_equals(cfg['section'], { 'name' : 'value' })
    assert_equals(cfg['section']['name'], 'value')
    ok_(isinstance(cfg, dict))

def test_meld():
    input1 = dedent("""
    [section1]
    key1 = value1
    key2 = value2
    """)
    input2 = dedent("""
    [section1]
    key1 = XXX
    key3 = value3

    [section2]
    key1 = value1
    """)
    expected = {
        'section1' : {
            'key1' : 'XXX', # cfg2 overwrites
            'key2' : 'value2',
            'key3' : 'value3', # cfg2 contributes
        },
        'section2' : { # cfg2 contributes
            'key1' : 'value1'
        }
    }
    cfg1 = Config.from_string(input1)
    cfg2 = Config.from_string(input2)
    cfg1.merge(cfg2)
    assert_equals(cfg1, expected)

def test_meld():
    input1 = dedent("""
    [section1]
    key1 = value1
    key2 = value2
    """)
    input2 = dedent("""
    [section1]
    key1 = XXX
    key3 = value3

    [section2]
    key1 = value1
    """)
    expected = {
        'section1' : {
            'key1' : 'value1',
            'key2' : 'value2',
            'key3' : 'value3',
        },
        'section2' : {
            'key1' : 'value1'
        }
    }
    cfg1 = Config.from_string(input1)
    cfg2 = Config.from_string(input2)
    cfg1.meld(cfg2)
    assert_equals(cfg1, expected)

def test_read():
    from glob import glob

    path = os.path.join(os.path.dirname(__file__), 'data', '*.conf')
    specs = os.path.join(os.path.dirname(__file__), 'data', '*.spec')
    for name in glob(path):
        Config.read([name])
    for name in glob(specs):
        Config.read([name])

def test_str():
    data = ("""
    [section]
    name = value
    """)

    cfg = Config.from_string(data)
    assert_equals(str(cfg), dedent(data).lstrip())


def test_write():
    path = os.path.join(os.path.dirname(__file__), 'data', 'mysqldump.conf')
    cfg = Config.read([path])
    dest = tempfile.mkdtemp()
    try:
        cfg.write(os.path.join(dest, 'foo.conf'))
        Config.read([os.path.join(dest, 'foo.conf')])
    finally:
        shutil.rmtree(dest)

def test_write_fileobj():
    input1 = dedent("""
    [section1]
    key1 = value1
    key2 = value2
    """)
    output = StringIO()
    cfg = Config.from_string(input1)
    cfg.write(output)
    Config.from_string(output.getvalue())
