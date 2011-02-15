
"""Generic support for loading file-like objects"""

from holland.core.stream.plugin import open_stream, available_methods, \
                                       load_stream_plugin, \
                                       StreamPlugin, StreamError
from holland.core.stream.base import FileLike, RealFileLike
