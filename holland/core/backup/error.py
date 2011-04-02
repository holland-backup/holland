"""
    holland.core.backup.error
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Standard exceptions raised by the Holland Backup API

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

class BackupError(Exception):
    """Raised when an error is encountered during a backup

    All BackupErrors should derive from this base class
    """

    def __init__(self, message, chained_exc=None):
        Exception.__init__(self, message)
        self.message = message
        self.chained_exc = chained_exc

    def __str__(self):
        msg = "%s" % self.message
        if self.chained_exc:
            msg += ": %s" % self.chained_exc
        return msg
