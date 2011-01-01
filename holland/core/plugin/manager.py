import logging
from pkg_resources import iter_entry_points
from error import PluginError, PluginNotFoundError

LOG = logging.getLogger(__name__)

class AbstractPluginManager(object):
    def load(self, name):
        """Load a plugin for the given name"""
        raise NotImplementedError()

    def iterate(self, name):
        """Iterate over plugins for the given name"""
        raise NotImplementedError()

class EntrypointPluginManager(AbstractPluginManager):
    def load(self, name):
        """Load a plugin via a setuptools entrypoint for the given name

        Name must be in the format group.name
        """
        group, name = name.rsplit('.', 1)

        for plugin in iter_entry_points(group, name):
            try:
                return plugin.load()
            except Exception, exc:
                raise PluginError(exc)
        raise PluginNotFoundError("No plugin found for group=%r name=%r" %
                                  (group, name))

    def iterate(self, name):
        group, name = name.rsplit('.', 1)
        for plugin in iter_entry_points(group, name):
            try:
                yield plugin.load()
            except Exception, exc:
                LOG.error("Failed to load plugin %r", plugin, exc_info=True)
                #raise PluginError(exc)

