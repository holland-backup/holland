"""
Core plugin support
"""

import logging
import os
import sys
from pkg_resources import working_set, Environment, iter_entry_points, \
                            find_distributions, \
                            DistributionNotFound, VersionConflict

LOGGER = logging.getLogger(__name__)

PLUGIN_DIRECTORIES = []

class PluginLoadError(Exception):
    """
    Place holder for PluginLoadError
    """
    pass

def add_plugin_dir(plugin_dir):
    """
    Find available plugins
    """
    if os.path.isdir(plugin_dir):
        return None
    LOGGER.debug("Adding plugin directory: %r", plugin_dir)
    env = Environment([plugin_dir])
    dists, errors = working_set.find_plugins(env)
    for dist in dists:
        LOGGER.debug("Adding distribution: %r", dist)
        working_set.add(dist)

    if errors:
        for dist, error in list(errors.items()):
            errmsg = None
            if isinstance(error, DistributionNotFound):
                req, = error.args
                errmsg = "%r not found" % req.project_name
            elif isinstance(error, VersionConflict):
                dist, req = error.args
                errmsg = "Version Conflict. Requested %s Found %s" % (req, dist)
            else:
                errmsg = repr(error)
            LOGGER.error("Failed to load %s: %r", dist, errmsg)
    PLUGIN_DIRECTORIES.append(plugin_dir)


def load_first_entrypoint(group, name=None):
    """
    load the first entrypoint in any distribution
    matching group and name
    """
    for entry_points in iter_entry_points(group, name):
        try:
            return entry_points.load()
        except DistributionNotFound as ex:
            raise PluginLoadError("Could not find dependency '%s'" % ex)
        except ImportError as ex:
            raise PluginLoadError(ex)
    raise PluginLoadError("'%s' not found" % '.'.join((group, name)))

def load_backup_plugin(name):
    """
    Pass name to load_first_entrypoint
    """
    return load_first_entrypoint('holland.backup', name)

def load_restore_plugin(name):
    """
    Pass name to load_first_entry_point
    """
    return load_first_entrypoint('holland.restore', name)

def get_commands(include_aliases=True):
    """
    Get list of avialable commands
    """
    cmds = {}
    for entry_point in iter_entry_points('holland.commands'):
        try:
            cmdcls = entry_point.load()
        except ImportError as ex:
            LOGGER.warning("Skipping command plugin %s: %s", entry_point.name, ex)
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
    for entry_point in working_set.iter_entry_points(group, name):
        yield entry_point.name, dist_metainfo_dict(entry_point.dist)

def dist_metainfo_dict(dist):
    """
    Convert an Egg's PKG-INFO into a dict
    """
    if sys.version_info > (3, 0):
        from email.parser import Parser
        from email.policy import default
        distmetadata = dist.get_metadata('PKG-INFO')
        ret = Parser(policy=default).parsestr(distmetadata)
    else:
        from rfc822 import Message # pylint: disable=import-error
        from cStringIO import StringIO # pylint: disable=import-error
        distmetadata = dist.get_metadata('PKG-INFO')
        msg = Message(StringIO(distmetadata))
        ret = dict(msg.items())
    return ret

def iter_plugininfo():
    """
    Iterate over the plugins loaded so far
    """
    if sys.version_info > (3, 0):
        from email.parser import Parser
        from email.policy import default
    else:
        from rfc822 import Message # pylint: disable=import-error
        from cStringIO import StringIO # pylint: disable=import-error
    for plugin_dir in PLUGIN_DIRECTORIES:
        for dist in find_distributions(plugin_dir):
            distmetadata = dist.get_metadata('PKG-INFO')
            if sys.version_info > (3, 0):
                msg = Parser(policy=default).parsestr(distmetadata)
            else:
                msg = Message(StringIO(distmetadata))
            filtered_keys = ['metadata-version', 'home-page', 'platform']
            distinfo = [x for x in list(msg.items()) if x[0] not in filtered_keys]
            yield dist, dict(distinfo)
