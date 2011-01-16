"""Standard exceptions raised by holland.core.backup"""

class BackupError(Exception):
    """Base exception all backup errors derive from"""

    def __init__(self, message, chained_exc=None):
        self.message = message
        self.chained_exc = chained_exc

    def __str__(self):
        msg = "%s" % self.message
        if self.chained_exc:
            msg += ": %s" % self.chained_exc
        return msg
