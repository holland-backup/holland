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


class MockPopen(object):
    """
    mock object to return to subclass.Popen
    """
    def __init__(self):
        self.pid = -1
        self.returncode = 0
        null = open(os.devnull, "w")
        self.stdin = null
        self.stderr = null
        self.stdout = null

    @staticmethod
    def wait():
        """
        Mock waiting for process to complete
        """
        return 0

    @staticmethod
    def poll():
        """
        Mock polling process status
        """
        return 0


class MockEnvironment(object):
    """
    Setup environement for dry-run
    """
    def __init__(self):
        """
        Create Mock object
        """
        self.mocker = MagicMock()

    def replace_environment(self):
        """
        Redirect everything to mock
        """
        self.mocker.replay()

    def restore_environment(self):
        """
        Return to normal environment
        """
        self.mocker.restore()
        self.mocker.verify()

    #pylint: disable=unused-argument
    @staticmethod
    def mocked_popen(*args, **kwargs):
        """
        Replace subprocess.peopen so dry-run doesn't
        actually call mysqldump
        """
        return MockPopen()
