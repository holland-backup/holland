"""
Core plugin support
"""

import logging
import os
import sys
try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

LOG = logging.getLogger(__name__)

PLUGIN_DIRECTORIES = []


class PluginLoadError(Exception):
    """
    Place holder for PluginLoadError
    """


def add_plugin_dir(plugin_dir):
    """
    Find available plugins
    """
    if os.path.isdir(plugin_dir):
        LOG.debug("Adding plugin directory: %r", plugin_dir)
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        PLUGIN_DIRECTORIES.append(plugin_dir)


def load_first_entrypoint(group, name=None):
    """
    load the first entrypoint in any distribution
    matching group and name
    """
    kwargs = {"group": group}
    if name is not None:
        kwargs["name"] = name
    for entry_point in metadata.entry_points(**kwargs):
        try:
            return entry_point.load()
        except ImportError as ex:
            raise PluginLoadError(ex)
    raise PluginLoadError("'%s' not found" % ".".join(filter(None, (group, name))))


def load_backup_plugin(name):
    """
    Pass name to load_first_entrypoint
    """
    return load_first_entrypoint("holland.backup", name)


def load_restore_plugin(name):
    """
    Pass name to load_first_entry_point
    """
    return load_first_entrypoint("holland.restore", name)


def get_commands(include_aliases=True):
    """
    Get list of avialable commands
    """
    cmds = {}
    for entry_point in metadata.entry_points(group="holland.commands"):
        try:
            cmdcls = entry_point.load()
        except ImportError as ex:
            LOG.warning("Skipping command plugin %s: %s", entry_point.name, ex)
            continue
        cmds[cmdcls.name] = cmdcls
        if include_aliases:
            for alias in cmdcls.aliases:
                cmds[alias] = cmdcls
    return cmds


def iter_plugins(group, name=None):
    """
    Iterate over all unique distributions defining
    entrypoints with the given group and name
    """
    kwargs = {"group": group}
    if name is not None:
        kwargs["name"] = name
    for entry_point in metadata.entry_points(**kwargs):
        yield entry_point.name, entry_point.dist.metadata
