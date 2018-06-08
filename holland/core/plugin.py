"""
Core plugin support
"""

import logging
import os
import sys
from pkg_resources import working_set, Environment, iter_entry_points, \
                            get_distribution, find_distributions, \
                            DistributionNotFound, VersionConflict

LOGGER = logging.getLogger(__name__)

plugin_directories = []

class PluginLoadError(Exception):
    pass

def add_plugin_dir(plugin_dir):
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
                # FIXME: Are there other types of failures?
                errmsg = repr(error)
            LOGGER.error("Failed to load %s: %r", dist, errmsg)
    global plugin_directories
    plugin_directories.append(plugin_dir)   


def load_first_entrypoint(group, name=None):
    """
    load the first entrypoint in any distribution
    matching group and name
    """
    for ep in iter_entry_points(group, name):
        try:
            return ep.load()
        except DistributionNotFound as e:
            raise PluginLoadError("Could not find dependency '%s'" % e)
        except ImportError as e:
            raise PluginLoadError(e)
    raise PluginLoadError("'%s' not found" % '.'.join((group, name)))

def load_backup_plugin(name):
    return load_first_entrypoint('holland.backup', name)

def load_restore_plugin(name):
    return load_first_entry_point('holland.restore', name)

def get_commands():
    cmds = {}
    for ep in iter_entry_points('holland.commands'):
        try:
            cmdcls = ep.load()
        except Exception as e:
            LOGGER.warning("Skipping command plugin %s: %s", ep.name, e)
            continue
        cmds[cmdcls.name] = cmdcls
        for alias in cmdcls.aliases:
            cmds[alias] = cmdcls
    return cmds

def iter_plugins(group, name=None):
    """
    Iterate over all unique distributions defining
    entrypoints with the given group and name
    """
    for ep in working_set.iter_entry_points(group, name):
        yield ep.name, dist_metainfo_dict(ep.dist)

def dist_metainfo_dict(dist):
    """Convert an Egg's PKG-INFO into a dict"""
    if sys.version_info > (3, 0):
        from email.parser import Parser
        from email.policy import default
        distmetadata = dist.get_metadata('PKG-INFO')
        return Parser(policy=default).parsestr(distmetadata)
    else:
        from rfc822 import Message
        from cStringIO import StringIO
        distmetadata = dist.get_metadata('PKG-INFO')
        msg = Message(StringIO(distmetadata))
        return dict(msg.items())

def iter_plugininfo():
    """
    Iterate over the plugins loaded so far
    """
    if sys.version_info > (3, 0):
        from email.parser import BytesParser, Parser
        from email.policy import default
    else:
        from rfc822 import Message
        from cStringIO import StringIO
    global plugin_directories
    for plugin_dir in plugin_directories:
        for dist in find_distributions(plugin_dir):
            distmetadata = dist.get_metadata('PKG-INFO')
            if sys.version_info > (3, 0):
                msg = Parser(policy=default).parsestr(distmetadata)
            else:
                msg = Message(StringIO(distmetadata))
            filtered_keys = ['metadata-version', 'home-page', 'platform']
            distinfo = [x for x in list(msg.items()) if x[0] not in filtered_keys]
            yield dist, dict(distinfo)
