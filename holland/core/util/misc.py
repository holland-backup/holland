"""Miscellaneous utility methods"""
try:
    from subprocess import Popen, PIPE
except ImportError:
    Popen = None
    PIPE = None

def run_command(cmd):
    """Run a command and get the stderr/stdout as a pair of strings

    :param cmd: string command
    :returns: 2-tuple (stdout_string, stderr_string)
    """
    if Popen is None:
        raise EnvironmentError("subprocess is not available")
    process = Popen(cmd,
                    shell=True,
                    stdout=PIPE,
                    stderr=PIPE,
                    close_fds=True)
    return process.communicate()
