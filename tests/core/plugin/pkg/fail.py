class NoopPlugin(object):
    def __init__(self, name):
        raise ValueError("This plugin will always raise an error on load")
