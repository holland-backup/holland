# $Id$

import sys,os
import tempfile
from shutil import rmtree
import pkg_resources
import helpers as _helpers 
import re


class Compression(object):
    def __init__(self):
        self.log = _helpers.get_logger(__name__)
        try:
            import tarfile as tarfile
            global tarfile
        except ImportError, e:
            self.log.warn(
                "tarfile module missing, gzip compression not available"
                )
            return None
        
        
class GzipCompression(Compression):
    def __init__(self):
        self.log = _helpers.get_logger(__name__)
        Compression.__init__(self)
        try:
            import gzip as gzip
            global gzip
        except ImportError, e:
            self.log.warn(
                "gzip module missing, gzip compression not available"
                )
            return None        
       
       
class BZ2Compression(Compression):
    def __init__(self):
        Compression.__init__(self)        
        try:
            import bz2
            from bz2 import BZ2File
            global bz2
        except ImportError, e:
            self.log.warn(
                'bz2 module missing, bzip2 compression not available'
                )     
            return None
            
            
class IOCompressionStream(Compression):
    def __init__(self, **kwargs):
        self.log = _helpers.get_logger(__name__)
        Compression.__init__(self)
        self.stream = None
        self.output_path = kwargs.get('output_path', None)
        
        assert not os.path.exists(self.output_path), \
            '%s already exists!' % self.output_path
        _helpers.ensure_dir(os.path.dirname(self.output_path))
        
    def open_stream(self):
        """
        Open a compressed stream for writing.  Must be subclassed.
        """
        raise "compression.IOCompressionStream.open_stream must be subclassed."
    
    def close_stream(self):
        """
        Close a compression stream.
        """
        raise "compression.IOCompressionStream.close_stream must be subclassed."
    
        
class GzipIOCompressionStream(IOCompressionStream,GzipCompression):      
    def __init__(self, **kwargs):
        self.log = _helpers.get_logger(__name__)
        IOCompressionStream.__init__(self, **kwargs)
        GzipCompression.__init__(self)
           
    def open_stream(self):
        """
        Open a Gzip compression stream for writing.  Returns an IO file
        handle object.
        """
        self.stream = gzip.open(self.output_path, 'w')
        self.log.debug('%s gzip io stream opened for writing' % self.stream)
        return self.stream
        
    def close_stream(self):
        """
        Close a Gzip compression stream.
        """
        # FIX ME: not sure what to catch here
        self.stream.close()
        self.log.debug('%s gzip io stream closed.' % self.stream)
        return True 
   
        
class BZ2IOCompressionStream(IOCompressionStream,BZ2Compression):      
    def __init__(self, **kwargs):
        self.log = _helpers.get_logger(__name__)
        IOCompressionStream.__init__(self, **kwargs)
        BZ2Compression.__init__(self)
        
    def open_stream(self):
        """
        Open a Bzip2 compression stream for writing.  Returns an IO file
        handle object.
        """
        self.stream = bz2.BZ2File(self.output_path, 'w')
        self.log.debug(
            '%s bzip2 io stream opened for writing' % self.output_path
            )
        return self.stream
        
    def close_stream(self):
        """
        Close a Bzip2 compression stream.
        """
        # FIX ME: not sure what to catch here
        self.stream.close()
        self.log.debug('%s bzip2 io stream closed.' % self.output_path)
        return True
                
                
class FileCompression(Compression):
    def __init__(self, **kwargs):
        Compression.__init__(self)
        self.log = _helpers.get_logger(__name__)
            
        self.source_path = kwargs.get('source_path', None)
        self.dest_dir = kwargs.get(
            'dest_dir', '%s/' % os.path.dirname(self.source_path)
            )
        self.compressed_path = None
        self.remove_source = kwargs.get('remove_source', False)
        self.compress_success = None
        self.decompress_success = None
        self.compressed_path = None
        self.decompressed_path = None
        
        # validations
        assert self.source_path, '%s missing'
        assert isinstance(self.remove_source, bool), \
            "remove_source must be True/False"

        assert os.path.exists(self.source_path), \
            '%s does not exist, skipping compression' % self.source_path
        
        # real paths please
        self.source_path = os.path.realpath(self.source_path)
        self.dest_dir = os.path.realpath(self.dest_dir)
        
        _helpers.ensure_dir(self.dest_dir)
            
    def compress(self):
        """
        Call all methods to perform compression.
        """
        self._pre_compress()
        self._compress_path()
        self._post_compress()
        
        if self.compress_success:
            return self.compressed_path
        else:
            return None
                 
    def decompress(self):
        """
        Call all methods to perform decompression.
        """
        self._pre_decompress()
        self._decompress_path()
        self._post_decompress()
        
        if self.decompress_success:
            return self.decompressed_path
        else:
            return None
          
    def _pre_compress(self):
        """
        This method is run before compression.
        """
        pass
        
    def _post_compress(self):
        """
        This method is run after compression.
        """
        if self.remove_source:
            self._remove_source_path()
    
    def _pre_decompress(self):
        """
        This method is run before decompression.
        """
        pass
    
    def _post_decompress(self):
        """
        This method is run after decompression.
        """
        if self.remove_source:
            self._remove_source_path()
        
    def _compress_path(self):
        """
        Compress directories or files.  Must be subclassed.
        """
        self.log.warn('_compress_path must be subclassed')

    def _decompress_path(self):
        """
        De-compress directories or files.  Must be subclassed.
        """
        pass
        
    def _remove_source_path(self):
        # FIX ME: need better checks here...  once we have a config to check
        # only delete if the file exists within the holland path or something?
        assert self.dest_dir != '/', 'trying to remove / (root)?'
        #try:
        #    rmtree(self.source_path)
        #    self.log.info('removed path %s' % self.source_path)
        #except IOError, e:
        #    self.log.error('failed to remove %s: %s' % (self.source_path, e))
        self.log.warn(
            'FIX ME -> compression.Compression._remove_source_path need ' +\
            'to properly write this method.'
            )
        if os.path.isfile(self.source_path):
            os.remove(self.source_path)
        elif os.path.isdir(self.source_path):
            rmtree(self.source_path)
        self.log.debug('removed path %s' % self.source_path)
           
              
class GzipFileCompression(FileCompression,GzipCompression):
    def __init__(self, **kwargs):
        FileCompression.__init__(self, **kwargs)
        GzipCompression.__init__(self)
        self.log = _helpers.get_logger(__name__)
        
    def _compress_path(self):
        """
        Compress directories or files using Gzip/Zlib libraries.
        """
        if os.path.isfile(self.source_path):
            self.compressed_path = os.path.join(
                self.dest_dir, "%s.gz" % os.path.basename(self.source_path)
                )
            try:
                f_in = open(self.source_path, "r")
                f_out = gzip.open(self.compressed_path, "w")
                f_out.write(f_in.read())
                f_in.close()
                f_out.close()
                self.log.debug(
                    "%s gzip'd as %s" % ( self.source_path, 
                                          self.compressed_path )
                    )
                self.compress_success = True
                
            except IOError, e:
                self.log.debug("failed to gzip %s" % self.source_path)
                
        elif os.path.isdir(self.source_path):
            self.compressed_path = os.path.join(
                self.dest_dir, "%s.tar.gz" % \
                    os.path.basename(self.source_path)
                )
            try:
                t = tarfile.open(name=self.compressed_path, mode = 'w:gz')
                t.add(self.source_path)
                t.close()
                self.log.debug(
                        "%s gzip'd as %s" % ( self.source_path, 
                                              self.compressed_path )
                        )
                self.compress_success = True
                
            except IOError, e:
                self.log.debug("failed to gzip %s" % self.source_path)
        
        else:
            self.log.warn(
                '%s is not a regular file/directory.  ignoring compression' %\
                self.source_path
                )
         
    def _decompress_path(self):
        """
        De-compress directories or files using Gzip/Zlib libraries.
        """
        self.decompressed_path = os.path.join(
                self.dest_dir, os.path.basename(self.source_path)
                )
        
        if self.decompressed_path.endswith('\.tar.gz'):
            self.decompressed_path = self.decompressed_path.split('.gz')[0]        
        elif self.decompressed_path.endswith('\.gz'):
            self.decompressed_path = self.decompressed_path.split('.gz')[0]
        elif self.decompressed_path.endswith('\.gz'):
            self.decompressed_path = self.decompressed_path.split('.gzip')[0]
            
        
        self.decompressed_path = _helpers.protected_path(
            self.decompressed_path
            )

        try:
            f_in = gzip.open(self.source_path, "r")
            f_out = open(self.decompressed_path, "w")
            f_out.write(f_in.read())
            f_in.close()
            f_out.close()
            
            # is it a tar?
            if tarfile.is_tarfile(self.decompressed_path):    
                tar_file = self.decompressed_path
                self.decompressed_path = self.decompressed_path.split('.tar')[0]
            
                self.decompressed_path = _helpers.protected_path(
                    self.decompressed_path
                    )

                try:
                    t = tarfile.open(name=tar_file, mode = 'r:')
                    t.extractall(self.decompressed_path)
                    t.close()
                    os.remove(tar_file)
        
                except IOError, e:
                    self.log.error(
                        "failed to untar %s (%s)" %\
                            (self.source_path, e)
                        )
                    
            self.log.debug(
                "%s gunzip'd as %s" % ( self.source_path, 
                                        self.decompressed_path )
                )
            self.decompress_success = True
            
        except IOError, e:
            self.log.error("failed to gunzip %s (%s)" % (self.source_path, e))
        
    
class BZ2FileCompression(FileCompression,BZ2Compression):
    def __init__(self, **kwargs):
        FileCompression.__init__(self, **kwargs)
        BZ2Compression.__init__(self)
        self.log = _helpers.get_logger(__name__)
                
    def _compress_path(self):
        """
        Compress directories or files using bz2(Bzip2) libraries.
        """
        if os.path.isfile(self.source_path):
            self.compressed_path = os.path.join(
                self.dest_dir, "%s.bz2" % os.path.basename(self.source_path)
                )
            try:
                f_in = open(self.source_path, "r")
                f_out = bz2.BZ2File(self.compressed_path, "w")
                f_out.write(f_in.read())
                f_in.close()
                f_out.close()
                self.log.debug(
                    "%s bzip2'd as %s" % ( self.source_path, 
                                          self.compressed_path )
                    )
                self.compress_success = True
                
            except IOError, e:
                self.log.error("failed to bzip2 %s" % self.source_path)
                
        elif os.path.isdir(self.source_path):
            self.compressed_path = os.path.join(
                self.dest_dir, "%s.tar.bz2" % \
                    os.path.basename(self.source_path)
                )
            try:
                t = tarfile.open(name=self.compressed_path, mode = 'w:bz2')
                t.add(self.source_path)
                t.close()
                self.log.debug(
                        "%s bzip2'd as %s" % ( self.source_path, 
                                              self.compressed_path )
                        )
                self.compress_success = True
                
            except IOError, e:
                self.log.error("failed to bzip2 %s" % self.source_path)
        
        else:
            self.log.warn(
                '%s is not a regular file/directory.  ignoring compression' %\
                self.source_path
                )
        
    def _decompress_path(self):
        """
        De-compress directories or files using bz2(Bzip2) libraries.
        """
        self.decompressed_path = os.path.join(
                self.dest_dir, '%s.bz2' % os.path.basename(self.source_path)
                )
                
        if self.decompressed_path.endswith('\.bz2'):
            self.decompressed_path = self.decompressed_path.split('.bz2')[0]
        elif self.decompressed_path.endswith('\.bzip2'):
            self.decompressed_path = self.decompressed_path.split('.bzip2')[0]
            
        
        self.decompressed_path = _helpers.protected_path(
            self.decompressed_path
            )

        try:
            f_in = bz2.BZ2File(self.source_path, "r")
            f_out = open(self.decompressed_path, "w")
            f_out.write(f_in.read())
            f_in.close()
            f_out.close()
            
            # is it a tar?
            if tarfile.is_tarfile(self.decompressed_path):    
                tar_file = self.decompressed_path
                self.decompressed_path = self.decompressed_path.split('.tar')[0]
            
                self.decompressed_path = _helpers.protected_path(
                    self.decompressed_path
                    )

                try:
                    t = tarfile.open(name=tar_file, mode = 'r:')
                    t.extractall(self.decompressed_path)
                    t.close()
                    os.remove(tar_file)
        
                except IOError, e:
                    self.log.error(
                        "failed to untar %s (%s)" %\
                            (self.source_path, e)
                        )
                    
            self.log.debug(
                "%s bunzip'd as %s" % ( self.source_path, 
                                        self.decompressed_path )
                )
            self.decompress_success = True
            
        except IOError, e:
            self.log.error("failed to bunzip %s (%s)" % (self.source_path, e))
    