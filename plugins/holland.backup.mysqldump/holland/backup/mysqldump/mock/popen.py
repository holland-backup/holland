# pylint: skip-file

"""Mock subprocess.Popen"""

from .mocker import *

def _debug_wait(*args, **kwargs):
    print("Waiting(args=%r, kwargs=%r)" % (args, kwargs))
    return 0

def mock_subprocess(mocker):
    popen = mocker.replace('subprocess.Popen')
    pid = popen(ARGS, KWARGS)
    mocker.count(min=0,max=None)

    pid.poll()
    mocker.count(min=0,max=None)
    mocker.result(0)

    pid.wait()
    mocker.count(min=0,max=None)
    mocker.result(0)

    foo = pid.returncode
    mocker.count(min=0,max=None)
    mocker.result(0)

    mock_subprocess_stdin(mocker, pid)
    mock_subprocess_stdout(mocker, pid)
    mock_subprocess_stderr(mocker, pid)

def mock_subprocess_stdin(mocker, pid):
    # mock stdin, stdout, stderr as iterate file-like objects
    pid.stdin.write(ANY)
    mocker.count(min=0,max=None)
    mocker.call(lambda s: len(s))

    pid.stdin.close()
    mocker.count(min=0,max=None)

def mock_subprocess_stdout(mocker, pid):
    pid.stdout.read(ANY)
    mocker.count(min=0, max=None)
    mocker.result('')
    iter(pid.stdout)
    mocker.count(min=0, max=None)
    mocker.generate('')

    pid.stdout.fileno()
    mocker.count(min=0,max=None)
    mocker.result(-1)

    pid.stdout.close()
    mocker.count(min=0,max=None)
    mocker.result(-1)

def mock_subprocess_stderr(mocker, pid):
    pid.stderr.read(ANY)
    mocker.count(min=0, max=None)
    mocker.result('')
    iter(pid.stderr)
    mocker.count(min=0, max=None)
    mocker.generate('')

    pid.stderr.fileno()
    mocker.count(min=0,max=None)
    mocker.result(-1)
