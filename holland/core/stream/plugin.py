"""
    holland.core.stream.plugin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the basic methods for the stream API

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

try:
    _set = set
except NameError: #pragma: no cover
    from sets import Set as _set

from holland.core.plugin import BasePlugin, PluginError, \
                                load_plugin, iterate_plugins


def load_stream_plugin(name):
    """Load a stream plugin by name"""
    return load_plugin('holland.stream', name)

def available_methods():
    """List available backup methods as strings

    These names are suitable for passing to open_stream(..., method=name, ...)
    """
    results = []
    for plugin in _set(iterate_plugins('holland.stream')):
        results.append(plugin.name)
        results.extend(plugin.aliases)
    return results

def open_stream(filename, mode='r', method=None, *args, **kwargs):
    """Open a stream with the provided method

    If not method is provided, this will default to the builtin file
    object
    """
    if method is None:
        method = 'file'
    try:
        stream = load_stream_plugin(method)
    except PluginError, exc:
        raise IOError("No stream found for method %r: %s" % (method, exc))
    return stream.open(filename, mode, *args, **kwargs)

class StreamPlugin(BasePlugin):
    """Base Plugin class"""
    name = ''
    aliases = ()

    def open(self, name, mode, method, *args, **kwargs):
        """Open a stream and return a FileLike instance"""
        if method is not None:
            raise StreamError("Invalid stream method '%s' for default Stream" %
                              method)
        return open(name, mode, *args, **kwargs)

    def stream_info(self, name, method, *args, **kwargs):
        """Provide information about this stream"""
        return dict(
            extension='',
            name=name,
            method=method,
            description="%s: args=%r kwargs=%r" % (self.__class__.__name__,
                                                   args, kwargs)
        )


class StreamError(IOError):
    """Exception in stream"""
