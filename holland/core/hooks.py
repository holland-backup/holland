"""Simple hook implementation

This module provides a convenience wrapper around dispatcher Signals
and provides the basis for a Hook plugin used in other places in the
holland backup framework
"""
from holland.core.plugin import ConfigurablePlugin

class BaseHook(ConfigurablePlugin):
    """Base hook class

    A hook is a simple callable that accepts informations about its caller -
    the sender id and the ``Signal``  instance - as well as additional
    keyword arguments accordingly the undelrying hook expectations

    ``BaseHook`` derives from ``holland.core.plugin.ConfigurablePlugin`` and
    is otherwise a standard Holland plugin.  Implementations should override
    the standard plugin methods (plugin_info(), configspec(), optionally
    configure()).  For plugin functionality an implementation can either
    override the ___call__ method or simply provide an execute method.

    execute(**kwargs) will be called by default and is useful if you don't
    really care what sender or signal is involved in the hook.
    """
    def __call__(self, sender, signal, **kwargs):
        self.execute(**kwargs)

    def execute(self, **kwargs):
        """Execute this hook"""

