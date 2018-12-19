"""Use Mock to preform dry run"""

import os
#For 2.7 or newer use unittest.mock
try:
    from unittest.mock import MagicMock, ANY
except ImportError:
    from mock import MagicMock, ANY

__all__ = [
    'MockEnvironment'
]


class mock_popen(object):
  def __init__(self, *args, **kwargs):
    self.pid = -1
    self.returncode = 0
    null = open(os.devnull,"w")
    self.stdin = null
    self.stderr = null
    self.stdout = null

  def wait(*args, **kwargs):
    return 0

  def poll(*args, **kwargs):
    return 0


class MockEnvironment(object):
    def __init__(self):
        self.mocker = MagicMock()

    def replace_environment(self):
        self.mocker.replay()

    def restore_environment(self):
        self.mocker.restore()
        self.mocker.verify()

    def mocked_popen(self, *args, **kwargs):
        return mock_popen(*args, **kwargs)
