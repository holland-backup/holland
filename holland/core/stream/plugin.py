"""Generic support for loading file-like objects"""

import os
try:
    set = set
except NameError:
    from sets import Set as set
try:
    SEEK_SET = os.SEEK_SET
    SEEK_CUR = os.SEEK_CUR
    SEEK_END = os.SEEK_END
except AttributeError:
    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2
from holland.core.plugin import BasePlugin, PluginError, PluginInfo, \
                                load_plugin, iterate_plugins


def load_stream_plugin(name):
    """Load a stream plugin by name"""
    return load_plugin('holland.stream', name)

def available_methods():
    """List available backup methods as strings

    These names are suitable for passing to open_stream(..., method=name, ...)
    """
    results = []
    for plugin in set(iterate_plugins('holland.stream')):
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
        stream = load_stream_plugin(method)(method)
    except PluginError, exc:
        raise IOError("No stream found for method %r: %s" % (method, exc))
    return stream.open(filename, mode, *args, **kwargs)

class StreamPlugin(BasePlugin):
    """Base Plugin class"""
    name = ''
    aliases = ()

    def __init__(self, name):
        self.name = name

    #@classmethod
    def open(cls, name, method, *args, **kwargs):
        raise NotImplementedError()
    open = classmethod(open)

    #@classmethod
    def stream_info(self, name, method, *args, **kwargs):
        return StreamInfo(
            extension='gz',
            name=name + '.gz',
            description="%s -%d" % (cmd, level)
        )
    stream_info = classmethod(stream_info)


class StreamInfo(dict):
    def __str__(self):
        return self.description

class StreamError(IOError):
    """Exception in stream"""
