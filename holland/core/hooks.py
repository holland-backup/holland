"""
    holland.core.hooks
    ~~~~~~~~~~~~~~~~~~

    Simple callback implementation that performs some action at
    different hook points.

    This module provides a convenience wrapper around dispatcher Signals
    and provides the basis for a Hook plugin used in other places in the
    holland backup framework

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import logging
from holland.core.plugin import ConfigurablePlugin, load_plugin, PluginError

LOG = logging.getLogger(__name__)

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

    ``execute(**kwargs)`` will be called by default and is useful if you don't
    really care what sender or signal is involved in the hook.
    """
    def configure(self, config):
        configspec = self.configspec()
        configspec['plugin'] = 'string'
        self.config = configspec.validate(config)

    def register(self, signal_group):
        """Register this hook with one or more signals in the signal group"""

    def __call__(self, sender, signal, **kwargs):
        return self.execute(**kwargs)

    def execute(self, **kwargs):
        """Execute this hook"""


def load_hooks_from_config(hooks, signal_group, config):
    """Initialize hooks based on the job config"""
    for name in hooks:
        hook_config = config.setdefault(name,
                                        config.__class__())
        try:
            hook_plugin = hook_config['plugin']
        except KeyError:
            LOG.error("Could not load hook %s - you must specify a "
                      "plugin in the [%s] section", name, name)
            continue

        try:
            hook = load_plugin('holland.hooks', hook_plugin)
        except PluginError, exc:
            LOG.error("Failed to load hook plugin '%s': %s", hook_plugin, exc)
            continue
        LOG.info("Configuring and register hook [%s] (plugin=holland.hooks.%s)",
                 name, hook_plugin)
        hook.configure(hook_config)
        hook.register(signal_group)
