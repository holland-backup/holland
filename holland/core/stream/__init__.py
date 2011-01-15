
"""Generic support for loading file-like objects"""

from holland.core.plugin import load_plugin, PluginError


def load_stream_plugin(name):
    """Load a stream plugin by name"""
    return load_plugin('holland.stream', name)

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
