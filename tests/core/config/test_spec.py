"""This module tests Configspec and validation"""
import os
from nose.tools import *
from holland.core.config import Config, Configspec

def test_spec():
    spec = Configspec({ 'foo' : Configspec({ 'bar' : 'integer', 'baz' : 'float'
        }) })
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
    assert_false(cfg.keys())

    spec = Configspec.read([path])
    spec.validate(cfg)
    assert_equals(cfg.keys(), spec.keys())
