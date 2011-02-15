"""Test the base File-like interfaces exposed by hollan.core.stream"""

import os, sys
from nose.tools import *
from holland.core.stream.base import *


def test_filelike():
    f = FileLike()

    ok_(not f.closed)
    # should be a noop
    f.flush()
    f.truncate()
    f.seek(0)

    # test abstract methods are abstract
    assert_raises(NotImplementedError, f.tell)

    # default returns EOF
    assert_raises(NotImplementedError, f.read)
    assert_raises(NotImplementedError, f.readline)
    assert_raises(NotImplementedError, f.readlines)
    assert_raises(NotImplementedError, f.next)

    f.close()
    ok_(f.closed)

    ok_(isinstance(PlainFile('/dev/null'), file))

    class Derived(FileLike):
        def readline(self):
            return 'foo'

        def read(self):
            return 'foo'

    f = Derived()
    assert_equals(f.next(), 'foo')

def test_realfilelike():
    class Derived(RealFileLike):
        def fileno(self):
            return os.pipe()[0]

    f = Derived()
    ok_(not f.isatty())
