# pylint: skip-file

import gc
import unittest
import builtins

import holland.backup.mysqldump.mock.storage as storage

dict_backend = storage.backend
FILE = '/myfile.txt'


class TestFileType(unittest.TestCase):
    def setUp(self):
        gc.collect()
        gc.collect()

    def test_patching(self):
        storage.replace_builtins()
        try:
            self.assertEqual(builtins.file, storage.file)
            self.assertEqual(builtins.open, storage.open)
        finally:
            storage.restore_builtins()

        self.assertEqual(builtins.file, storage.original_file)
        self.assertNotEqual(storage.original_file, storage.file)
        self.assertEqual(builtins.open, storage.original_open)
        self.assertNotEqual(storage.original_open, storage.open)


    def test_file_simple_read_and_write(self):
        source_data = 'Some text\nwith newlines\n'

        handle = storage.file(FILE, 'w')
        self.assertEqual(handle.mode, 'w')
        handle.write(source_data)
        handle.close()

        handle = storage.file(FILE,'r')
        data = handle.read()
        self.assertEqual(handle.mode, 'r')
        handle.close()
        self.assertEqual(data, source_data)

        handle = storage.file(FILE)
        self.assertEqual(handle.mode, 'r')
        data = handle.read()
        handle.close()
        self.assertEqual(data, source_data)


    def test_open_simple_read_and_write(self):
        source_data = 'Some text\nwith newlines\n'

        handle = storage.open(FILE, 'w')
        self.assertTrue(isinstance(handle, storage.file))
        self.assertEqual(handle.mode, 'w')
        handle.write(source_data)
        handle.close()

        handle = storage.open(FILE, 'r')
        self.assertTrue(isinstance(handle, storage.file))
        data = handle.read()
        self.assertEqual(handle.mode, 'r')
        handle.close()
        self.assertEqual(data, source_data)

        handle = storage.open(FILE)
        self.assertTrue(isinstance(handle, storage.file))
        self.assertEqual(handle.mode, 'r')
        data = handle.read()
        handle.close()
        self.assertEqual(data, source_data)


    def test_read_to_write(self):
        handle = storage.file(FILE, 'w')
        handle.write('some new data')
        handle.close()

        h = storage.file(FILE)
        self.assertRaises(IOError, h.write, 'foobar')


    def test_write_to_read(self):
        h = storage.file(FILE, 'w')
        self.assertRaises(IOError, h.read)


    def test_multiple_writes(self):
        handle = storage.file(FILE, 'w')
        handle.write('foo')
        handle.write('bar')
        handle.close()

        self.assertEqual(storage.file(FILE).read(), 'foobar')


    def test_repr(self):
        write = storage.file(FILE, 'w')
        read = storage.file(FILE, 'r')
        string = '<open file %r mode %r>'
        self.assertEqual(repr(read), string % (FILE, 'r'))
        self.assertEqual(repr(write), string % (FILE, 'w'))

        string = '<closed file %r mode %r>'
        write.close()
        read.close()
        self.assertEqual(repr(read), string % (FILE, 'r'))
        self.assertEqual(repr(write), string % (FILE, 'w'))


    def test_invalid_mode(self):
        self.assertRaises(ValueError, storage.file, 'filename', 'q')
        self.assertRaises(ValueError, storage.file, 'filename', '')
        self.assertRaises(TypeError, storage.file, 'filename', None)
        self.assertRaises(TypeError, storage.file, 'filename', 3)


    def test_open_nonexistent_file(self):
        self.assertRaises(IOError, storage.file, FILE + FILE, 'r')


    def test_open_write_deletes_and_creates(self):
        handle = storage.file(FILE, 'w')
        self.assertEqual(storage.file(FILE).read(), '')
        handle.write('foobar')
        handle.close()

        handle = storage.file(FILE, 'w')
        self.assertEqual(storage.file(FILE).read(), '')


    def test_gc_closes(self):
        handle = storage.file(FILE, 'w')
        handle.write('some new data')
        del handle
        gc.collect()
        gc.collect()
        self.assertEqual(storage.file(FILE).read(), 'some new data')


    def foo_closed(self):
        handle = storage.file(FILE, 'w')
        self.assertFalse(handle.closed)

        handle.close()
        self.assertTrue(handle.closed)

        self.assertRaises(ValueError, handle.write, 'foo')

        handle = storage.file(FILE)
        self.assertFalse(handle.closed)

        handle.close()
        self.assertTrue(handle.closed)

        self.assertRaises(ValueError, handle.read)


    def test_read_seek_tell(self):
        storage._store.clear()
        h = storage.file(FILE, 'w')
        h.write('foobar')
        h.close()

        h = storage.file(FILE)
        self.assertEqual(h.tell(), 0)

        self.assertEqual(h.read(0), '')
        self.assertEqual(h.read(1), 'f')
        self.assertEqual(h.tell(), 1)
        h.seek(0)
        self.assertEqual(h.tell(), 0)
        self.assertEqual(h.read(1), 'f')

        self.assertEqual(h.read(), 'oobar')
        self.assertEqual(h.read(), '')

        h.seek(0)
        self.assertEqual(h.read(100), 'foobar')

        h.seek(1000)
        self.assertEqual(h.tell(), 1000)
        self.assertEqual(h.read(100), '')

        self.assertRaises(IOError, h.seek, -1)
        self.assertRaises(TypeError, h.seek, None)

        # test deprecation warning for float value?


    def test_write_seek_tell(self):
        h = storage.file(FILE, 'w')
        self.assertEqual(h.tell(), 0)

        h.write('f')
        self.assertEqual(h.tell(), 1)
        h.seek(2)
        self.assertEqual(h.tell(), 2)
        h.write('g')
        h.close()
        self.assertEqual(storage.file(FILE).read(), 'f\x00g')

        h = storage.file(FILE, 'w')
        h.write('f')
        h.seek(0)
        h.write('g')
        h.close()
        self.assertEqual(storage.file(FILE).read(), 'g')

        h = storage.file(FILE, 'w')
        h.seek(1000)
        h.write('g')
        h.close()

        expected = '\x00' * 1000 + 'g'
        self.assertEqual(storage.file(FILE).read(), expected)

        self.assertRaises(IOError, h.seek, -1)
        self.assertRaises(TypeError, h.seek, None)


    def test_flush(self):
        h = storage.file(FILE, 'w')
        h.write('foo')

        read_handle = storage.file(FILE)
        self.assertEqual(read_handle.read(), '')

        h.flush()
        self.assertEqual(read_handle.read(), 'foo')
        h.close()

        self.assertRaises(IOError, read_handle.flush)
        read_handle.close()


    def test_read_write_binary(self):
        h = storage.file(FILE, 'w')
        h.write('foo\nbar\n')
        h.close()

        h = storage.file(FILE)
        self.assertEqual(h.read(), 'foo\nbar\n')
        h.close()

        h = storage.file(FILE, 'rb')
        self.assertEqual(h.read(), 'foo\r\nbar\r\n')
        h.close()

        h = storage.file(FILE, 'wb')
        h.write('foo\nbar\n')
        h.close()

        h = storage.file(FILE, 'rb')
        self.assertEqual(h.read(), 'foo\nbar\n')
        h.close()

        h = storage.file(FILE, 'w')
        h.write('foo\nbar\n')
        h.close()

        h = storage.file(FILE, 'rb')
        self.assertEqual(h.read(), 'foo\r\nbar\r\n')
        h.close()


    def test_assorted_members(self):
        h = storage.file(FILE, 'w')
        self.assertEqual(h.encoding, None)
        self.assertEqual(h.errors, None)
        self.assertEqual(h.newlines, None)
        self.assertFalse(h.isatty())
        h.close()

        h = storage.file(FILE)
        self.assertEqual(h.encoding, None)
        self.assertEqual(h.errors, None)
        self.assertEqual(h.newlines, None)
        self.assertFalse(h.isatty())
        h.close()


    def test_fileno(self):
        h = storage.file(FILE, 'w')
        h2 = storage.file(FILE)
        fileno1 = h.fileno()
        fileno2 = h2.fileno()

        self.assertTrue(isinstance(fileno1, int))
        self.assertTrue(isinstance(fileno2, int))

        self.assertTrue(fileno1 > 2)
        self.assertTrue(fileno2 > 2)

        self.assertNotEqual(fileno1, fileno2)

        h.close()
        h2.close()


    def test__iter__(self):
        # not as hard as you might think
        h = storage.file(FILE, 'w')
        i = h.__iter__()
        self.assertTrue(h is i)
        h.close()


    def test_next(self):
        h = storage.file(FILE, 'w')
        h.write('foo\nbar\nbaz\n')
        self.assertRaises(IOError, h.__next__)
        h.close()

        h = storage.file(FILE)
        self.assertEqual(next(h), 'foo\n')

        self.assertRaises(ValueError, h.read)

        self.assertEqual(next(h), 'bar\n')
        self.assertEqual(next(h), 'baz\n')
        self.assertRaises(StopIteration, h.__next__)
        h.close()

        h = storage.file(FILE)
        self.assertEqual(next(h), 'foo\n')
        h.seek(1)
        self.assertEqual(next(h), 'oo\n')

        h.seek(3)
        self.assertEqual(h.read(4), '\nbar')
        self.assertEqual(next(h), '\n')


    def test_readline(self):
        h = storage.file(FILE, 'w')
        h.write('foo\nbar\nbaz\n')
        self.assertRaises(IOError, h.readline)
        h.close()

        h = storage.file(FILE)
        self.assertEqual(h.readline(), 'foo\n')
        self.assertEqual(h.tell(), 4)
        h.seek(0)
        self.assertEqual(h.readline(), 'foo\n')

        self.assertRaises(TypeError, h.readline, None)
        self.assertEqual(h.readline(0), '')
        self.assertEqual(h.readline(1), 'b')
        self.assertEqual(h.readline(100), 'ar\n')
        self.assertEqual(h.tell(), 8)
        self.assertEqual(h.readline(-1), 'baz\n')
        self.assertEqual(h.tell(), 12)
        self.assertEqual(h.readline(), '')
        self.assertEqual(h.tell(), 12)
        h.close()


    def test_readlines(self):
        h = storage.file(FILE, 'w')
        h.write('foo\nbar\nbaz\n')
        self.assertRaises(IOError, h.readlines)
        h.close()

        h = storage.file(FILE)
        self.assertEqual(h.readlines(), ['foo\n', 'bar\n', 'baz\n'])
        self.assertEqual(h.readlines(), [])
        h.seek(0)

        self.assertRaises(TypeError, h.readline, None)
        self.assertEqual(h.readlines(0), ['foo\n', 'bar\n', 'baz\n'])
        h.close()

    def test_xreadlines(self):
        h = storage.file(FILE, 'w')
        self.assertTrue(h is h)
        h.close()


    def test_softspace(self):
        h = storage.file(FILE, 'w')
        h.softspace = 1
        h.write('blam')
        self.assertEqual(h.softspace, 0)

        def set_softspace():
            h.softspace = 'kablooie'
        self.assertRaises(TypeError, set_softspace)

        h.close()


    def test_truncate(self):
        h = storage.file(FILE, 'w')
        h.write('kabloooie')

        self.assertRaises(IOError, storage.file(FILE).truncate)
        self.assertRaises(TypeError, h.truncate, 'foo')
        self.assertRaises(IOError, h.truncate, -1)

        h.seek(3)
        h.truncate()
        self.assertEqual(storage.file(FILE).read(), 'kab')

        h.truncate(10)
        self.assertEqual(storage.file(FILE).read(), 'kab\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(h.tell(), 3)

        h.truncate(2)
        self.assertEqual(h.tell(), 3)
        h.close()


    def test_writelines(self):
        h = storage.file(FILE, 'w')


        self.assertRaises(IOError, storage.file(FILE).writelines, [])
        self.assertRaises(TypeError, h.writelines, object())

        h.write('blah')
        h.writelines(['\n','q', 'w', 'e'])
        h.close()

        f = storage.file(FILE)
        data = f.read()
        f.close()
        self.assertEqual(data, 'blah\nqwe')

    def test_append_mode(self):
        source_data = 'Some text\nwith newlines\n'
        storage._store.clear()
        handle = storage.open(FILE, 'ab')
        try:
            f = storage.open(FILE)
            try:
                self.assertEqual(f.read(), '')
            finally:
                f.close()

            handle.write(source_data)
        finally:
            handle.close()

        handle = storage.open(FILE, 'rb')
        try:
            self.assertEqual(handle.read(), source_data)
        finally:
            handle.close()

        handle = storage.open(FILE, 'a')
        try:
            self.assertEqual(handle.tell(), len(source_data))
            handle.write(source_data[::-1])
        finally:
            handle.close()

        handle = storage.open(FILE)
        try:
            self.assertEqual(handle.read(), source_data + source_data[::-1])
        finally:
            handle.close()


    def test_read_write_mode(self):
        #self.assertRaises(IOError, storage.file, FILE, 'r+')

        h = storage.file(FILE, 'w')
        h.__enter__()
        try:
            h.write('foo')
        finally:
            h.__exit__()

        h = storage.file(FILE, 'r+')
        h.__enter__()
        try:
            self.assertEqual(h.tell(), 0)
            self.assertEqual(h.read(), 'foo')
            self.assertEqual(h.tell(), 3)
            h.write('bar')
            self.assertEqual(h.tell(), 6)
            h.seek(0)
            self.assertEqual(h.read(), 'foobar')
        finally:
            h.__exit__()

    def test_write_read_mode(self):
        f = storage.file(FILE, 'w')
        try:
            f.write('foo')
        finally:
            f.close()

        h = storage.file(FILE, 'w+')
        try:
            f = storage.file(FILE)
            try:
                self.assertEqual(f.read(), '')
            finally:
                f.close()

            self.assertEqual(h.read(), '')
            self.assertEqual(h.tell(), 0)
            h.write('foo')
            self.assertEqual(h.tell(), 3)
            self.assertEqual(h.read(), '')

            h.seek(0)
            self.assertEqual(h.read(), 'foo')
        finally:
            h.close()


    def test_append_read_mode(self):
        f = storage.file(FILE, 'w')
        try:
            f.write('foo')
        finally:
            f.close()

        h = storage.file(FILE, 'a+')
        try:
            f = storage.file(FILE)
            try:
                self.assertEqual(f.read(), 'foo')
            finally:
                f.close()

            self.assertEqual(h.tell(), 3)
            self.assertEqual(h.read(), '')
            h.write('bar')
            self.assertEqual(h.tell(), 6)
            self.assertEqual(h.read(), '')

            h.seek(0)
            self.assertEqual(h.read(), 'foobar')
        finally:
            h.close()


    def test_seek_with_whence(self):
        data = 'foo bar baz'
        h = storage.file(FILE, 'w')
        try:
            h.write(data)
        finally:
            h.close()

        h = storage.file(FILE)
        self.assertRaises(IOError, h.seek, 0, 3)
        self.assertRaises(IOError, h.seek, -1, 0)
        self.assertRaises(IOError, h.seek, 0, -1)
        self.assertRaises(TypeError, h.seek, 0, None)

        h.seek(3, 0)
        self.assertEqual(h.tell(), 3)

        h.seek(-3, 1)
        self.assertEqual(h.tell(), 0)
        self.assertRaises(IOError, h.seek, -1, 1)

        h.seek(3, 1)
        self.assertEqual(h.tell(), 3)

        h.seek(0, 2)
        self.assertEqual(h.tell(), len(data))

        h.seek(-2, 2)
        self.assertEqual(h.tell(), len(data) - 2)

        h.seek(2, 2)
        self.assertEqual(h.tell(), len(data) + 2)
        self.assertRaises(IOError, h.seek, -(len(data) + 1), 2)


    def test_read_only_attributes(self):
        def setter(attribute, value):
            return lambda: setattr(h, attribute, value)

        h = storage.file(FILE, 'w')
        try:
            self.assertRaises(AttributeError, setter('mode', 'w'))
            self.assertRaises(AttributeError, setter('name', 'foo2'))
            self.assertRaises(AttributeError, setter('closed', True))
            self.assertRaises(AttributeError, setter('encoding', 'ascii'))
            self.assertRaises(AttributeError, setter('errors', None))
            self.assertRaises(AttributeError, setter('newlines', 'foo'))
        finally:
            h.close()


    def test_read_negative(self):
        h = storage.file(FILE, 'w')
        try:
            h.write('foo bar baz')
        finally:
            h.close()

        h = storage.file(FILE)
        try:
            self.assertEqual(h.read(-3), 'foo bar baz')
        finally:
            h.close()


    def test_invalid_name(self):
        self.assertRaises(IOError, storage.file, '')
        self.assertRaises(IOError, storage.file, '', 'w')
        self.assertRaises(TypeError, storage.file, None)
        self.assertRaises(TypeError, storage.file, None, 'w')
        self.assertRaises(TypeError, storage.file, 3)


    def test_default_backend(self):
        storage.backend = dict_backend
        storage._store.clear()

        self.assertRaises(IOError, storage.file, FILE)

        h = storage.file(FILE, 'w')
        h.__enter__()
        try:
            h.write('foo')
        finally:
            h.__exit__()

        h = storage.file(FILE)
        h.__enter__()
        try:
            self.assertEqual(h.read(), 'foo')
        finally:
            h.__exit__()


"""
Differences from standard file type:

* Attempting to set the read-only attributes (like mode, name etc) raises an AttributeError
  rather than a TypeError
* The exception messages are not all identical (some are better!)
* Strict about modes. Unrecognised modes always raise an exception

  (NOTE: The exception method that the standard file type does throw is:
   "ValueError: mode string must begin with one of 'r', 'w', 'a' or 'U', not 'z'")

* The deprecated readinto is not implemented

TODO:

* The buffering argument to the constructor is not implemented
* The IOError exceptions raised don't have an associated errno
* encoding, errors and newlines do nothing
* Behavior of tell() and seek() for text mode files may be incorrect (it
  should treat '\n' as '\r\n')
* Behaves like Windows, writes '\n' as '\r\n' unless in binary mode. A global
  flag to control this?
* Universal modes not supported
* Missing __format__ method needed when we move to 2.6
* Implementations of os and os.path that work with storage_backend
"""
