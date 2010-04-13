"""Engine harness for connecting parser output with
external systems"""

# XXX: Cleanup pydoc
class RestoreEngine(object):
    """Pull data from a parser and write to file object.
    
    If an update callable is specified, it will be called
    every time loop is called with the current parser
    and other information.
    """
    def __init__(self, parser, fileobj, update=None):
        self.parser = parser
        self.update = update
        self._buffer = ''

    def loop(self, timeout=1.0):
        if self._buffer:
            ret = select(wfds=[fileobj.fileno()], timeout=timeout)
            if ret > 0:
                count = fileobj.write(self._buffer)
                self._buffer = self._buffer[count:]
        else:
            self._buffer += self.parser.step()
        if self.update:
            self.update(parser, self.written)

        
