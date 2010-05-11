[compression]
-------------

Specify various compression settings, such as compression utility,
compression level, etc.

**method** = gzip | pigz | bzip | lzop | lzma 

    Define which compression method to use. Note that ``lzop`` and 
    ``lzma`` may not be available on every system and may need to be compiled 
    / installed.
    
**inline** = yes | no

    Whether or not to pipe the output of mysqldump into the compression
    utility. Enabling this is recommended since it usually only marginally
    impacts performance, particularly when using a lower compression
    level.
    
**level** = 0-9

    Specify the compression ratio. The lower the number, the lower the 
    compression ratio, but the faster the backup will take. Generally,
    setting the lever to 1 or 2 results in favorable compression of 
    textual data and is noticeably faster than the higher levels.
    Setting the level to 0 effectively disables compression.
    
**bin-path** = <full path to utility>

    This only needs to be defined if the compression utility is not in the
    usual places or not in the system path.
