"""Miscellaneous utility methods"""
from subprocess import Popen, PIPE

def run_command(cmd):
    """Run a command and get the stderr/stdout as a pair of strings

    :param cmd: string command
    :returns: 2-tuple (stdout_string, stderr_string)
    """
    try:
        process = Popen(cmd,
                        shell=True,
                        stdout=PIPE,
                        stderr=PIPE,
                        close_fds=True)
    except OSError, exc:
        raise

    stdout, stderr = process.communicate()

    return stdout, stderr
