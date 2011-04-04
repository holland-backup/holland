"""
    holland.core.plugin.manager
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Plugin manager API responsible for loading plugins

    :copyright: 2008-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

import pkgutil
import logging
import pkg_resources
from holland.core.plugin.util import import_module
from holland.core.plugin.error import PluginError, PluginLoadError, \
                                      PluginNotFoundError
from holland.core.plugin.base import BasePlugin

LOG = logging.getLogger(__name__)

class AbstractPluginManager(object):
    """PluginManager interface

    All plugin managers should implement two methods:
        * load(group, name) - load a plugin given a group and a name
        * iterate(group) - iterate over all plugins in a given group

    Plugin managers are free to interpret ``group`` and ``name`` according to
    their own implementations.  ``EntrypointPluginManager`` loads these per the
    pkg_resources.iter_entry_points API but other managers may be added in the
    future that will work off simpler __import__ system and treat ``group`` as
    a package name and ``name`` as an attribute defined in the package.
    """

    def load(self, group, name):
        """Load a plugin for the given name

        The default behaviors raises ``PluginNotFoundError`` exception and
        should be overriden by real implementation in a subclass
        """
        raise PluginNotFoundError(group, name)

    def iterate(self, group):
        """Iterate over plugins for the given name

        The default behavior returns an empty list.
        """
        if group or not group:
            return []

class ImportPluginManager(AbstractPluginManager):
    """Plugin manager that uses __import__ to load a plugin

    This is an example of a PluginManager that loads modules through a simple
    __import__() protocol and iterates over available plugins in a package via
    python's ``pkgutil`` module
    """

    def load(self, group, name):
        """Load a plugin from a module named by ``group``.``name`` looks for an
        attribute on that module called ``name``.

        For example mysqldump might be a module holland.backup.mysqldump which
        defines a ``mysqldump`` attribute pointing to a ``BasePlugin``
        subclass::
            holland/backup/mysqldump.py:
                mysqldump = MyMySQLDumpPlugin

        This is designed after the pattern used by sqlalchemy's dialect plugin
        system.

        :raises: ``PluginNotFoundError`` if no plugin is found on the
                 module defined by group.name
        :returns: instance of BasePlugin if found
        """
        module = import_module('.'.join(group, name))
        try:
            return module.getattr(name, module)
        except AttributeError:
            raise PluginNotFoundError("No such plugin %s.%s" % (group, name))

    def iterate(self, group):
        """Iterate over plugins in the package named by ``group``

        This implementation uses pkgutil to walk the packages under the pkg
        namespace named by the ``group`` argument and yields any subclasses of
        ``BasePlugin`` found in that package.
        """
        module = import_module(group)
        for _, name in pkgutil.walk_packages(module.__path__):
            submodule = import_module(group + '.' + name)
            plugin = getattr(submodule, name)
            if isinstance(plugin, BasePlugin):
                yield plugin(name)

class EntrypointPluginManager(AbstractPluginManager):
    """Plugin manager that uses setuptools entrypoints"""

    def load(self, group, name):
        """Load a plugin via a setuptools entrypoint for the given name

        Name must be in the format group.name
        """
        # These typically give no information about what was going on froma
        # str(exc) alone:
        # DistributionNotFoundError - A requested distribution was not found
        # VersionConflict - An already-installed version conflicts with the
        #                   requested version
        # These are raised when an entrypoint has declared dependencies
        for plugin in pkg_resources.iter_entry_points(group, name):
            try:
                return plugin.load()(plugin.name)
            except (SystemExit, KeyboardInterrupt):
                raise
            except pkg_resources.DistributionNotFound, exc:
                raise EntrypointDependencyError(group, name,
                                                entrypoint=plugin,
                                                req=exc.args[0])
            except pkg_resources.VersionConflict, exc:
                raise EntrypointVersionConflictError(group, name,
                                                     entrypoint=plugin,
                                                     req=exc.args[1])
            except Exception, exc:
                LOG.exception("Exception when loading plugin")
                raise PluginLoadError(group, name, exc)
        raise PluginNotFoundError(group, name)

    def iterate(self, group):
        """Iterate over an entrypoint group and yield the loaded entrypoint
        object
        """
        for plugin in pkg_resources.iter_entry_points(group):
            try:
                yield plugin.load()(plugin.name)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                LOG.error("Failed to load plugin %r from group %s",
                          plugin, group, exc_info=True)

# specific to entrypoint plugins
class EntrypointDependencyError(PluginError):
    """An entrypoint or its python egg distribution requires some dependency
    that could not be found by setuptools/pkg_resources

    :attr entrypoint:  entrypoint that causes this error
    :attr req: requirement that could not be found
    """

    def __init__(self, group, name, entrypoint, req):
        PluginError.__init__(self, group, name, None)
        self.entrypoint = entrypoint
        self.req = req

    def __str__(self):
        return "Could not find dependency '%s' for plugin %s in group %s" % \
               (self.req, self.name, self.group)

class EntrypointVersionConflictError(PluginError):
    """Raises when multiple egg distributions provide the same requirement but
    have different versions.
    """

    def __init__(self, group, name, entrypoint, req):
        PluginError.__init__(self, group, name, None)
        self.entrypoint = entrypoint
        self.dist = entrypoint.dist
        self.req = req

    def __str__(self):
        return ("Version Conflict while loading plugin package. "
                "Requested %s Found %s" % (self.req, self.dist))
