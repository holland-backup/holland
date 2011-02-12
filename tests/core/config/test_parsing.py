"""Test parsing of the configspec check DSL"""
from nose.tools import *
from holland.core.config.check import CheckParser

def test_simple():
    name, args, kwargs = CheckParser.parse('integer')
    assert_equals(name, 'integer')
    assert_equals(args, ())
    assert_equals(kwargs, {})

def test_args():
    name, args, kwargs = CheckParser.parse('foo(bar,baz,biz)')
    assert_equals(name, 'foo')
    assert_equals(args, ('bar', 'baz', 'biz'))
    assert_equals(kwargs, {})

def test_kwargs():
    name, args, kwargs = CheckParser.parse('foo(bar=baz, baz=boz)')
    assert_equals(name, 'foo')
    assert_equals(args, ())
    assert_equals(kwargs, { 'bar' : 'baz', 'baz' : 'boz' })

def test_quoted():
    name, args, kwargs = CheckParser.parse('foo("bar","baz", biz)')
    assert_equals(name, 'foo')
    assert_equals(args, ('bar', 'baz', 'biz'))
    assert_equals(kwargs, {})

def test_none():
    name, args, kwargs = CheckParser.parse('foo(None, bar, baz, default=None)')
    assert_equals(name, 'foo')
    assert_equals(args, (None, 'bar', 'baz'))
    assert_equals(kwargs, { 'default' : None })

def test_list_values():
    check = 'foo(bar, baz, list(foo, bar, baz))'
    name, args, kwargs = CheckParser.parse(check)
    assert_equals(name, 'foo')
    assert_equals(args, ('bar', 'baz', ['foo', 'bar', 'baz']))
