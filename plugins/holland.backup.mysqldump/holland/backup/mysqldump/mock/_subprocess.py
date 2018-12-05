# pylint: skip-file

from .storage import original_open as open

class PopenMock(object):
    """subprocess.Popen mock object implementation

    This does not support the new features in 2.6
    (kill, send_signal, terminate)
    """
    def __init__(self, *args, **kwargs):
        self.pid = -1
        self.stdin = open("/dev/null", "r")
        self.stdout = open("/dev/null", "r+")
        self.stderr = open("/dev/null", "r+")
        self.returncode = None
        self.universal_newlines = False

    def communicate(self, input=None):
        """Interact with the process"""
        return ('', '')

    def wait(self):
        """Wait for this process to finish.

        This mock objects always returns 0 for the status
        """
        if self.returncode is None:
            self.returncode = 0
        return self.returncode

    def poll(self):
        if self.returncode is None:
            self.returncode = 0
        return self.returncode
