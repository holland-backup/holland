"""
    holland.core.util.signal
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Signal container to group signal instances from holland.core.dispatch

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import logging
from holland.core.dispatch import Signal

LOG = logging.getLogger(__name__)

class SignalGroup(dict):
    """Simple Signal container"""
    def __init__(self, names):
        dict.__init__(self)
        for name in names:
            self[name] = Signal()

    def notify_safe(self, name, **kwargs):
        """Send a notification all all receivers for a signal name

        No exception will be raised but an iterable for all results
        collected from listeners will be returned.  On error a result
        will be a subclass of Exception

        :returns: iterable of results
        """
        signal = self[name]
        for receiver, result in signal.send_robust(sender=None,
                                                   event=name,
                                                   **kwargs):
            yield result

    def notify_all(self, name, **kwargs):
        """Send notifications to the named signal in this SignalGroup

        This sends the notification to all listeners in the group.  If any
        raises an exception then an exception will be raised at the end.
        """
        for result in self.notify_safe(name, **kwargs):
            if isinstance(result, Exception):
                LOG.debug("Received (%r) raised an exception: %r",
                          receiver, result)
                raise result

    def notify(self, name, **kwargs):
        """Send notifications al the named signal in this SignalGroup

        This sends a notification but an error will be raised immediately
        and will abort the notification process.

        This method may not send the signal to all registered receivers.
        """
        self[name].send(sender=None, event=name, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key.replace('_', '-')]
        except KeyError:
            raise AttributeError('%r object has no attribute %r' %
                                 (self.__class__.__name__, key))
