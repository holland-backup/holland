from holland.core.plugin.util import import_module
from nose.tools import *

def test_bad_import():
    assert_raises(ImportError, import_module, 'foo_bar_baz')

def test_relative_import():
    import_module('.backup', 'holland.core')
    assert_raises(TypeError, import_module, '.backup')
    assert_raises(ValueError, import_module, '..', 'holland')

def test_bad_package_arg():
    assert_raises(ValueError, import_module, '.backup', package=42)
