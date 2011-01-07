"""Plugin manager API"""

import logging
from pkg_resources import iter_entry_points
from holland.core.plugin.error import PluginError, PluginNotFoundError

LOG = logging.getLogger(__name__)

class AbstractPluginManager(object):
    """Interface that PluginManager implementations should follow"""

    def load(self, group, name):
        """Load a plugin for the given name"""
        raise NotImplementedError()

    def iterate(self, group, name):
        """Iterate over plugins for the given name"""
        raise NotImplementedError()

class EntrypointPluginManager(AbstractPluginManager):
    """Plugin manager that uses setuptools entrypoints"""

    def load(self, group, name):
        """Load a plugin via a setuptools entrypoint for the given name

        Name must be in the format group.name
        """
        for plugin in iter_entry_points(group, name):
            try:
                return plugin.load()
            except Exception, exc:
                LOG.exception("Exception when loading plugin")
                raise PluginError(exc)
        raise PluginNotFoundError("No plugin found for %s.%s" % (group, name))

    def iterate(self, group):
        """Iterate over an entrypoint group and yield the loaded entrypoint
        object
        """
        for plugin in iter_entry_points(group):
            try:
                yield plugin.load()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                LOG.error("Failed to load plugin %r", plugin, exc_info=True)

