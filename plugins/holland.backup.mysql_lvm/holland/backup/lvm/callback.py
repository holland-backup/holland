"""Implement priority-based callbacks"""

try: # pragma: no cover
    set
except NameError: # pragma: no cover
    from sets import Set as set

__all__ = [
    'CallbackDelegate'
]

class CallbackDelegate(object):
    """A simple callback interface with callback priority"""

    def __init__(self):
        self.listeners = dict(
        )
        self._priorities = {}
        
    def add_callback(self, channel, callback, priority=None):
        """Add the given callback at the given channel (if not present)."""
        if channel not in self.listeners:
            self.listeners[channel] = set()
        self.listeners[channel].add(callback)

        if priority is None:
            priority = getattr(callback, 'priority', 50)
        self._priorities[(channel, callback)] = priority
        
    def remove_callback(self, channel, callback):
        """Discard given callback (if present)."""
        listeners = self.listeners.get(channel)
        if listeners and callback in listeners:
            listeners.discard(callback)
            del self._priorities[(channel, callback)]
    
    def run_callback(self, channel, *args, **kwargs):
        """Return output of all subscribers for the given channel."""
        output = []
        for result in self.run_one_callback(channel, *args, **kwargs):
            output.append(result)
        return output

    def run_one_callback(self, channel, *args, **kwargs):
        """Yield result of each subscriber for the given channel."""
        if channel not in self.listeners:
            return

        items = [(self._priorities[(channel, listener)], listener)
                 for listener in self.listeners[channel]]
        items.sort()

        for priority, listener in items:
            priority = priority
            try:
                result = listener(*args, **kwargs)
            except: 
                # FIXME: Avoid an early abort?
                raise
            else:
                yield result
