import os
import shutil
from nose.tools import *
from tempfile import mkdtemp

from holland.core.exceptions import ArgumentError
from holland.lib import compression

global tmpdir, config, plugin

def setup_func():
    global tmpdir
    tmpdir = mkdtemp()

def teardown_func():
    global tmpdir
    shutil.rmtree(tmpdir)
    
@with_setup(setup_func, teardown_func)
def test_lookup_compression():
    global tmpdir
    
    # should get something back, None if the method wasn't found
    cmd, ext = compression.lookup_compression('gzip')
    assert_not_equal(cmd, None)
    assert_not_equal(ext, None)
    
    # should get something back, None if the method wasn't found
    cmd, ext = compression.lookup_compression('bzip2')
    assert_not_equal(cmd, None)
    assert_not_equal(ext, None)
    
    # should get something back, None if the method wasn't found
    cmd, ext = compression.lookup_compression('lzop')
    assert_not_equal(cmd, None)
    assert_not_equal(ext, None)
    
    # this should fail
    cmd, ext = compression.lookup_compression('bogus_compression')
    assert_equal(cmd, None)
    assert_equal(ext, None)
    
@with_setup(setup_func, teardown_func)
def test_compression():
    global tmpdir
    
    # gzip - write it, read it, verify it
    f = compression.open_stream(os.path.join(tmpdir, 'gzip_foo'), 'w', 'gzip')
    f.write('foo')
    f.close()
    
    f = compression.open_stream(os.path.join(tmpdir, 'gzip_foo'), 'r', 'gzip')
    foo = f.read(3)
    f.close()

    ok_(foo == 'foo')
    
    # bzip2 - write it, read it, verify it
    f = compression.open_stream(os.path.join(tmpdir, 'bzip2_foo'), 'w', 'bzip2')
    f.write('foo')
    f.close()
    
    f = compression.open_stream(os.path.join(tmpdir, 'bzip2_foo'), 'r', 'bzip2')
    foo = f.read(3)
    f.close()

    ok_(foo == 'foo')
    
    # gzip - write it, read it, verify it
    f = compression.open_stream(os.path.join(tmpdir, 'lzop_foo'), 'w', 'lzop')
    f.write('foo')
    f.close()
    
    f = compression.open_stream(os.path.join(tmpdir, 'lzop_foo'), 'r', 'lzop')
    foo = f.read(3)
    f.close()

    ok_(foo == 'foo')
    
@raises(IOError)    
@with_setup(setup_func, teardown_func)
def test_compression_wrong_method():
    global tmpdir
    
    # gzip - write it, read it, verify it
    f = compression.open_stream(os.path.join(tmpdir, 'foo'), 'w', 'gzip')
    f.write('foo')
    f.close()
    
    f = compression.open_stream(os.path.join(tmpdir, 'foo'), 'r', 'bzip2')
    foo = f.read(3)
    f.close()

@raises(ArgumentError)
@with_setup(setup_func, teardown_func)
def test_compression_bad_mode():
    global tmpdir

    f = compression.open_stream(os.path.join(tmpdir, 'foo'), 'w', 'gzip')
    f.write('foo')
    f.close()
    
    f = compression.open_stream(os.path.join(tmpdir, 'foo'), 'bad', 'gzip')
    f.write('foo')
    f.close()
    
    