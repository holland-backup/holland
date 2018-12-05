""" Example plugin test """

import time
from holland.backup.example import ExamplePlugin
from nose.tools import assert_equals, ok_

# Config mock, so we don't have to import holland.core
class MockConfig(object):
    """ Example mock configuration object """

    def validate(self, spec):
        """ Example validation method """
        pass

def test_example_plugin():
    """ Example driver function """
    name = 'example/' + time.strftime('%Y%m%d_%H%M%S')
    target_directory = '/tmp/example_backup/'
    config = MockConfig()
    dry_run = False

    plugin = ExamplePlugin(name, config, target_directory, dry_run)
    assert_equals(plugin.estimate_backup_size(), 0)
    plugin.backup()

    dry_run = True

    plugin = ExamplePlugin(name, config, target_directory, dry_run)
    plugin.backup()

    ok_(isinstance(plugin.info(), str))
