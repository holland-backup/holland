"""Test Holland hooks"""

import sys
from mocker import *
from nose.tools import *
from textwrap import dedent
from holland.core import PluginError
from holland.core import Config
from holland.core.dispatch import Signal
from holland.core.hooks import *

class ExampleHook(BaseHook):
    def __init__(self, name):
        super(ExampleHook, self).__init__(name)
        self.actions = ['init']

    def configure(self, config):
        super(ExampleHook, self).configure(config)
        self.actions.append('configure')

    def register(self, signal_group):
        BaseHook.configure(self, signal_group)
        self.actions.append('register')
        signal_group.faux_signal.connect(self, weak=False)

    def execute(self, *args, **kwargs):
        self.actions.append('execute')
        return self

class FauxSignalGroup(dict):
    def __init__(self):
        dict.__init__(self)
        self.faux_signal = Signal()

mock = Mocker()

def setup():
    def faux_load_plugin(group, name):
        if name == 'baz':
            raise PluginError("As a conscientious objector, I refuse to load "
                              "the baz plugin for test coverage reasons")
        return ExampleHook(name)
    load_plugin = mock.replace('holland.core.plugin.load_plugin')
    load_plugin(ARGS, KWARGS)
    mock.call(lambda group, name: faux_load_plugin(group, name))
    mock.count(min=1, max=None)
    mock.replay()

def teardown():
    mock.restore()

def test_load_hooks_from_config():
    cfg = Config.parse(dedent("""
    [foo]
    plugin = example
    setting = foo-a-bar

    [bar]
    plugin = bar
    param = bar-a-foo

    [baz]
    plugin = baz
    option = foo-a-baz
    """).splitlines())

    sg = FauxSignalGroup()

    load_hooks_from_config(['does-not-exist', 'foo', 'bar', 'baz'], sg, cfg)

    for recv, response in sg.faux_signal.send(sender=None, arg='foo'):
        # this test should not raise any errors
        ok_(not isinstance(response, Exception))
        # we should hit all of the parts of the hook lifecycle
        assert_equals(recv.actions,
                      ['init', 'configure', 'register', 'execute'])
