import sys, os
import platform
import unittest
import tempfile
import string
import random
import logging
import logging.handlers as handlers
import md5
from shutil import rmtree

# FIXME: This used to test holland.helpers which was
#        a collection of utility methods. These have
#        since been forked off into various plugins
#        or merged into holland.core.util. This
#        should be updated to test holland.core.util
#        and any other tests added to the appropriate
#        plugin egg's test suite.

#class TestSysUtilsHelper(unittest.TestCase):
# hack: disabling test until I fix
# many of these functions have been shuffled around
# into individual plugins and need merged into those
# test cases
class Test(object):
    """
    A test class for testing the sysutils helper
    """
    
    def setUp(self):
        self.log = logging.getLogger('holland')
        file = logging.FileHandler(filename='/dev/null')
        self.log.addHandler(file)
        
    
    def test_ensure_dir(self):
        # No arguments
        self.assertRaises(TypeError, h.ensure_dir);
        # Directory that already exists
        self.assertEqual(h.ensure_dir('/tmp'), True)
        # File that already exists
        self.assertEqual(h.ensure_dir('/dev/null'), True)
        # Directory that does not exist
        self.assertEqual(h.ensure_dir('/tmp/testdir'), True)
        # Directory that cannot be created
        self.assertRaises(OSError, h.ensure_dir, '/dev/null/dir')
        # Cleanup
        os.rmdir('/tmp/testdir')


    def test_protected_path(self):
        # file
        fd,file_path = tempfile.mkstemp(prefix='holland-test-')
        safe_path = h.protected_path(file_path)
        expected_path = "%s.0" % file_path
        self.assertEquals(safe_path == expected_path, True)
        
        # dir
        dir_path = tempfile.mkdtemp(prefix='holland-test-')
        safe_path = h.protected_path(dir_path)
        expected_path = "%s.0" % dir_path
        self.assertEquals(safe_path == expected_path, True)
        
        # clean up
        os.remove(file_path)
        rmtree(dir_path)
    
    def test_get_compression_stream(self):
        for c_mode in ['gzip', 'bzip2']:
            fd,file_path = tempfile.mkstemp(prefix='holland-test-')
            dir_path = tempfile.mkdtemp(prefix='holland-test-dir')        
            file_path = os.path.realpath(file_path)
            os.remove(file_path)
            dir_path = os.path.realpath(dir_path)
            data = ''
            for i in xrange(1024**2):
                data = data + random.choice(string.letters)
        
            stream = h.get_compression_stream(output_path=file_path, mode=c_mode)
            stream.write(data)
            stream.close()
        
            new_file_path = h.decompress_path(
                source_path=file_path, dest_dir=dir_path, mode=c_mode
                )

            f = open(new_file_path, 'r')
            a = md5.new(f.read()).digest()
            b = md5.new(data).digest()
            self.assertEqual(a == b, True)    
            f.close()

            # clean up 
            os.remove(new_file_path)
            rmtree(dir_path)
        
    def test_compress_path(self):
        # Test to see if a file can be gzipped and ungzipped
        # (and it returns the same md5sum)
        fd,file_path = tempfile.mkstemp(prefix='holland-test-')
        dir_path = tempfile.mkdtemp(prefix='holland-test-dir')        
        file_path = os.path.realpath(file_path)
        dir_path = os.path.realpath(dir_path)
        
        # Create and compress the file
        handle = os.fdopen(fd, 'w')
        for i in xrange(1024**2):
            handle.write(random.choice(string.letters))
        handle.close()
        comp_path = h.compress_path(
            source_path = file_path, dest_dir = dir_path, 
            remove_source = False, mode = 'gzip'
            )
                                  
        self.assertEqual(comp_path != None, True)
        
        # Uncompress the file and compare to original
        uncomp_path = h.decompress_path(
            source_path = comp_path, dest_dir = dir_path, 
            remove_source = False, mode = 'gzip'
            )
        self.assertEqual(uncomp_path != None, True)

        original_file = file(file_path)
        uncompressed_file = file(uncomp_path)
        
        a = md5.new(original_file.read()).digest()
        b = md5.new(uncompressed_file.read()).digest()
        self.assertEqual(a == b, True)
        
    
    # Platform-specific tests
    #   FIX ME:
    #       Tests are incomplete and have not been tested on Linux platform
    
    def test_mount_info(self):
        self.assertRaises(TypeError, h.mount_info)
        if platform.system() != 'Linux':
            print "Skipping Test For This Platform (%s)" % platform.system()
            return False
            
    def test_which(self):
        # No arguments given
        self.assertRaises(TypeError, h.which)
        if platform.system() == 'Windows':
            print "Skipping Test For This Platform (%s)" % platform.system()
            return False
        # Common utility test
        self.assertEqual(h.which('ls'), '/bin/ls')
        # Not found test
        self.assertRaises(OSError, h.which, 'notacommand')
        
    # FIX ME: Incomplete Test
    def test_relpath(self):
        # No arguments given
        self.assertRaises(TypeError, h.relpath)
        if platform.system() == 'Windows':
            print "Skipping Test For This Platform (%s)" % platform.system()
            return False
        # Same Path
        self.assertEqual(h.relpath('test', 'test'), '')        
        # Empty Path
        self.assertEqual(h.relpath('', ''), '')
        # Sub-Path
        self.assertEqual(h.relpath('/tmp/test', '/test'), None)
        
    # End of platform-specific tests

    def test_format_bytes(self):
        # No arguments given
        self.assertRaises(TypeError, h.format_bytes)
        # 0 bytes
        self.assertEqual(h.format_bytes(0), '0.00B')
        # 1b
        self.assertEqual(h.format_bytes(1), '1.00B')
        # 1KiB
        self.assertEqual(h.format_bytes(1024), '1.00KiB')
        # Remaing test for other units.
        # Note the + 2 since we ran the '1b' and '1KiB' tests above
        # and these were taken from the array in the original function
        units = ['MiB','GiB','TiB','PiB','EiB','ZiB','YiB']
        for unit in units:
            power = units.index(unit) + 2
            self.assertEqual(h.format_bytes(1024**power),
                            '1.00' + unit)
        # Negative Bytes
        self.assertRaises(ArithmeticError, h.format_bytes, -1);


    def tearDown(self):
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSysUtilsHelper))
    return suite

if __name__ == '__main__':
    unittest.main()
    unittest.TextTestRunner(verbosity=3).run(suite())
