# pylint: skip-file

import time
from holland.backup.example import ExamplePlugin
from nose.tools import *

# Config mock, so we don't have to import holland.core
class MockConfig(object):
    def validate(self, spec):
        pass

def test_example_plugin():
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
