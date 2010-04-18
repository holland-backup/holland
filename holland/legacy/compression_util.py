    
def get_compression_stream(**kwargs):
    """
    Open a compressed data stream.  Expects the following params:
    
        output_path = output file path
        mode = compression mode - gzip, bzip2, ...
    
    Returns:
    
        stream = compression.IOCompressionStream object
    
    Example:
    
        >>> stream = helpers.get_compression_stream(
                output_path='/tmp/myfile.gz', mode='gzip'
                )
        >>> stream.write('data... data... data...')
        >>> stream.close()
        
    """
    log = get_logger(__name__)
    output_path = kwargs.get('output_path', None)
    mode = kwargs.get('mode')
    
    assert mode in ['gzip', 'bzip2'], \
        "%s is not a supported compression mechanism."
    
    if mode == 'gzip':
        c = compression.GzipIOCompressionStream(output_path=output_path) 

    elif mode == 'bzip2':
        c = compression.BZ2IOCompressionStream(output_path=output_path) 
    c.open_stream()    
    return c.stream
       
def compress_path(**kwargs):
    """
    Compress a file or directory path.  Expects the following params:
    
        source_path = source directory or file to compress
        dest_dir = destination directory to save the compressed file
        remove_source = True/False - removes original source if True
        mode = compression mode - gzip, bzip2, ...
        
    Returns:
        
        string  - compressed file path on success
        None    - on failure
    """
    log = get_logger(__name__)
    source_path = kwargs.get('source_path', None)
    dest_dir = kwargs.get('dest_dir', os.path.dirname(source_path))
    mode = kwargs.get('mode', 'gzip').lower()
    remove_source = kwargs.get('remove_source', False)

    assert mode in ['gzip', 'bzip2'], \
        "%s is not a supported compression mechanism."
    
    if mode == 'gzip':
        c = compression.GzipFileCompression(
            source_path=source_path, dest_dir=dest_dir, 
            remove_source=remove_source
            )        

    elif mode == 'bzip2':
        c = compression.BZ2FileCompression(
            source_path=source_path, dest_dir=dest_dir, 
            remove_source=remove_source
            )        

    if c.compress():
        return c.compressed_path
    else:
        log.error('compressing path %s seems to have failed' % source_path)
        return None
    
def decompress_path(**kwargs):
    """
    Decompress a file or directory path.  Accepts the following params:
    
        source_path = source directory or file to decompress
        dest_dir = destination directory to save the decompressed file/dir
        remove_source = True/False - removes original source if True
        mode = gzip, bzip2, ...
        
    Returns:
        
        string  - decompressed file or directory path on success
        None    - on failure
        
    """
    log = get_logger(__name__)
    source_path = kwargs.get('source_path', None)
    dest_dir = kwargs.get('dest_dir', os.path.dirname(source_path))
    mode = kwargs.get('mode', None)
    remove_source = kwargs.get('remove_source', False)

    if not mode:
        if source_path.endswith('.gz') or source_path.endswith('gzip'):
            mode = 'gzip'
        elif source_path.endswith('.bzip2') or source_path.endswith('bz2'):
            mode = 'bzip2'    
    
    assert str(mode).lower() in ['gzip', 'bzip2'], \
        "%s is not a supported compression mechanism." % mode
    
    if mode == 'gzip':
        c = compression.GzipFileCompression(
            source_path=source_path, dest_dir=dest_dir, 
            remove_source=remove_source
            )        
    elif mode == 'bzip2':
        c = compression.BZ2FileCompression(
            source_path=source_path, dest_dir=dest_dir, 
            remove_source=remove_source
            )
    if c.decompress():
        return c.decompressed_path
    else:
        log.error('decompressing path %s seems to have failed' % source_path)
        return None
        
