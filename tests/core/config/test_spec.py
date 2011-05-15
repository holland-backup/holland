"""This module tests Configspec and validation"""
import os
from nose.tools import *
from holland.core.config import Config, Configspec, ValidateError

def test_spec():
    spec = Configspec.from_string('''
    [foo]
    bar = integer
    baz = float
    ''')
    data = { 'foo' : { 'bar' : '32', 'baz' : '3.14159' } }
    data = spec.validate(data)
    assert_equals(data['foo']['bar'], 32)
    assert_equals(data['foo']['baz'], 3.14159)

def test_validate_missing():
    # run validation against an object with missing
    # values that the spec should provide via default
    # values
    path = os.path.join(os.path.dirname(__file__),
                        'data',
                        'mysqldump.spec')
    cfg = Config()
    ok_(not cfg.keys())

    spec = Configspec.read([path])
    spec.validate(cfg)
    assert_equals(cfg.keys(), spec.keys())

def test_unknown_check():
    spec = Configspec.from_string('''
    [bar]
    oompa = loompa
    ''')

    assert_raises(ValidateError, spec.validate, Config())

def test_source_merge():
    foo = Config.from_string('''
    [test]
    foo = bar
    ''')

    foo.name = 'main_config'

    spec = Configspec.from_string('''
    [bar]
    oompa = string(default="loompa")
    ''')

    spec.name = 'configspec'

    base_cfg = spec.validate(Config())
    foo.meld(base_cfg)
    assert_equals(foo['bar'].source, base_cfg['bar'].source)
