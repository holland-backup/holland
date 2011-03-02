import sys

class Foo(object):
    def __init__(self, name):
        # test error handling by plugin manager
        sys.exit(1)
