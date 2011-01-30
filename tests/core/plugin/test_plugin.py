"""Test the holland plugin api"""
from pkg_resources import FileMetadata, Distribution, working_set
from nose.tools import *
from holland.core.plugin import *

# some mock methods we might use
#XXX: Generate simple problems like DistributionError/etc. with no error
# message and validate we get a useful response back from the plugin api
class MockMetadata(FileMetadata):
    def __init__(self, path):
        self.path = path

    def has_metadata(self, name):
        return name in ('PKG-INFO', 'entry_points.txt')

    def get_metadata(self, name):
        if name == 'PKG-INFO':
            return ''
        if name == 'entry_points.txt':
            # this should be something unlikely to conflict
            # with normal entrypoints elsewhere
            return """
            [holland.plugin]
            foo     = pkg:Bar
            noop    = pkg.fail:NoopPlugin

            [holland.error]
            exit    = pkg.exctest:Foo
            """
        raise KeyError("MockMetadata: %s" % name)

import os, sys
# ensure our test pkg 'pkg' is importable
sys.path.append(os.path.dirname(__file__))
distribution = Distribution('pkg',
                            project_name='pkgtest',
                            metadata=MockMetadata('pkg'))
working_set.add(distribution)


def test_load_plugin():
    plugin = load_plugin('holland.plugin', 'foo')
    assert_equals(plugin.name, 'foo')

    assert_equals([plugin.__name__ for plugin in
                   iterate_plugins('holland.plugin')],
                  ['Bar'])

    assert_raises(PluginError, load_plugin, 'holland.plugin', 'noop')

    # ensure plugin api doesn't swallow the errors
    assert_raises(SystemExit, load_plugin, 'holland.error', 'exit')
    assert_raises(SystemExit, lambda: [x for x in iterate_plugins('holland.error')])

    assert_raises(PluginNotFoundError, load_plugin, 'holland.plugin', 'xyzzy')
