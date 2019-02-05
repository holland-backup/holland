"""Standard errors raised by holland.lib.lvm"""


class SnapshotError(Exception):
    """Error occurred during snapshotting process"""


class LVMCommandError(Exception):
    """Error occurred while running a lvm command

    :attribute cmd: The command that was being run
    :attribute status: exit status of the command
    :attribute error: stderr output of the command
    """

    def __init__(self, cmd, status, error):
        error = error.strip() if error else ""
        Exception.__init__(self, cmd, status, error)
        self.cmd = cmd
        self.status = status
        self.error = error

    def __str__(self):
        return "Command '%s' exited with status %d" % (self.cmd, self.status)
