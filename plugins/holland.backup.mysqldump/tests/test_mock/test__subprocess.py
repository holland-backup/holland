# pylint: skip-file

from holland.backup.mysqldump.mock._subprocess import PopenMock
from holland.backup.mysqldump.mock import MockEnvironment
from nose.tools import assert_equals

def test_popen_communicate():
    pid = PopenMock(['echo', 'foo'], close_fds=True)
    result = pid.communicate()
    assert_equals(result, ('',''))
