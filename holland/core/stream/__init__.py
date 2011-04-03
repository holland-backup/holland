"""
    holland.core.stream
    ~~~~~~~~~~~~~~~~~~~

    Stream plugin API for Holland.

    Stream plugins provide a way to transform output of file or file-like
    objects. This generally means redirecting output of some command through
    compression or encryption filters through a standard API.

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from holland.core.stream.plugin import open_stream, available_methods, \
                                       load_stream_plugin, \
                                       StreamPlugin, StreamError
from holland.core.stream.base import FileLike, RealFileLike

__all__ = [
    'open_stream',
    'available_methods',
    'load_stream_plugin',
    'StreamPlugin',
    'StreamError',
]
