from nose.tools import *
from holland.lib.lvm.base import *

def test_basevolume():
    assert_raises(NotImplementedError, Volume)

    class Test(Volume):
        pass

    ok_(Test())

    volume = Test({ 'foo' : 'bar', 'baz' : 'biz' })
    assert_equals(volume.foo, 'bar')
    assert_equals(volume.baz, 'biz')
    assert_raises(AttributeError, volume.__getattr__, 'blah')

    assert_raises(NotImplementedError, volume.reload)
    assert_raises(NotImplementedError, Test.lookup, 'foo')
    assert_raises(NotImplementedError, Test.search, 'foo')

    assert_equals(repr(Test()), 'Test()')
