# pylint: skip-file

import logging
#For 2.7 or newer use unittest.mock
try:
    from unittest.mock import MagicMock, ANY
except ImportError:
    from mock import MagicMock, ANY
from . import storage
from ._subprocess import PopenMock

LOG = logging.getLogger(__name__)


class SpecialArgument(object):
    """Base for special arguments for matching parameters."""

    def __init__(self, object=None):
        self.object = object

    def __repr__(self):
        if self.object is None:
            return self.__class__.__name__
        else:
            return "%s(%r)" % (self.__class__.__name__, self.object)

    def matches(self, other):
        return True

    def __eq__(self, other):
        return type(other) == type(self) and self.object == other.object


class ARGS(SpecialArgument):
    """Matches zero or more positional arguments."""

ARGS = ARGS()


class KWARGS(SpecialArgument):
    """Matches zero or more keyword arguments."""

KWARGS = KWARGS()


class MATCH(SpecialArgument):

    def matches(self, other):
        return bool(self.object(other))

    def __eq__(self, other):
        return type(other) == type(self) and self.object is other.object


class MockEnvironment(object):
    def __init__(self):
        self.mocker = MagicMock()
        _setup_fileio(self.mocker)
        _setup_mysqlclient(self.mocker)
        _setup_subprocess(self.mocker)

    def replace_environment(self):
        self.mocker.replay()

    def restore_environment(self):
        # restore MySQLClient
        # restore normal file io
        # restore normal subprocess
        self.mocker.restore()

def _setup_fileio(mocker):
    """Patch __builtin__.open.

    Allow read access normally, but all writes go
    through the storage mock layer.
    """
    def is_writemode(param):
        """Check whether a open() mode will allow a write operation"""
        return 'a' in param or 'w' in param

    # this doesn't handle r+ properly, but we don't use it in mysqldump
    _open = mocker.replace('builtins.open')
    fileobj = _open(ANY, MATCH(is_writemode), ANY)
    mocker.count(min=0,max=None)
    mocker.call(storage.open)

    fileobj = _open(ANY, MATCH(is_writemode))
    mocker.count(min=0,max=None)
    mocker.call(storage.open)

    _mkdir = mocker.replace('os.mkdir')
    _mkdir(ARGS)
    mocker.count(min=0,max=None)

def _setup_mysqlclient(mocker):
    """Patch any dangerous methods on MySQLClient

    Used for dry-run support.  Currently avoid
    doing stop_slave or start_slave in dry-run mode
    but allow all other (read) operations.
    """
    connect = mocker.replace("holland.lib.mysql.client.base.connect")
    client = connect(ARGS, KWARGS)

    client.connect()
    mocker.count(min=0,max=None)
    client.disconnect()
    mocker.count(min=0,max=None)
    # replace stop_slave, start_slave
    client.stop_slave(ARGS, KWARGS)
    mocker.count(min=0,max=None)
    client.start_slave()
    mocker.count(min=0,max=None)

def match_mysqldump(param):
    LOG.debug("match_mysqldump %r", param)
    if param and 'mysqldump' in param[0]:
        return "--version" in param
    return False

def _setup_subprocess(mocker):
    """Patch subprocess.Popen with a Mock object.

    In dry-run mode, don't run any commands - just
    fake it.
    """
    popen = mocker.replace("subprocess.Popen")
    pid = popen(MATCH(match_mysqldump), KWARGS)
    mocker.count(min=0,max=None)
    mocker.passthrough()

    pid = popen(ARGS, KWARGS)
    mocker.count(min=0,max=None)
    mocker.call(PopenMock)
