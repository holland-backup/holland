"""
    holland.core.util.misc
    ~~~~~~~~~~~~~~~~~~~~~~

    Miscellaneous utility methods

    :copyright: 2008-2010 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

try:
    from subprocess import Popen, PIPE
except ImportError:
    Popen = None
    PIPE = None

def run_command(cmd):
    """Run a command and get the stderr/stdout as a pair of strings

    This method always runs a command via a shell, does not leak file
    descriptors to the child process and returns the stdout and stderr
    of that child process.

    This method should only be used when the output from a command is
    reasonably small as all the output is spooled in memory as a python
    string.

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
