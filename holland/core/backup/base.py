"""Standard Holland Backup API classes"""

import logging
from holland.core.plugin import ConfigurablePlugin
from holland.core.config import Configspec

LOG = logging.getLogger(__name__)

class BackupError(Exception):
    """Raised when an error is encountered during a backup

    All BackupErrors should derive from this base class
    """

    def __init__(self, message, chained_exc=None):
        self.message = message
        self.chained_exc = chained_exc

    def __str__(self):
        msg = "%s" % self.message
        if self.chained_exc:
            msg += ": %s" % self.chained_exc
        return msg

class BackupPlugin(ConfigurablePlugin):
    """Interface that Holland Backup Plugins should conform to"""

    def pre(self):
        """Run before starting a backup"""

    def estimate(self):
        """Estimate the size of the backup this plugin would produce"""
        raise NotImplementedError()

    def backup(self):
        """Backup to the specified path"""
        raise NotImplementedError()

    def dryrun(self):
        """Perform a dry-run backup to the specified path"""
        raise NotImplementedError()

    def post(self):
        """Run after a backup"""

    def backup_info(self):
        """Provide information about this backup"""
        raise NotImplementedError()

    #@staticmethod
    def configspec():
        from textwrap import dedent
        return Configspec.parse(dedent("""
        [holland:backup]
        plugin                  = string
        auto-purge-failures     = boolean(default=yes)
        purge-policy            = option("manual",
                                         "before-backup",
                                         "after-backup",
                                         default="after-backup")
        backups-to-keep         = integer(default=1)
        estimated-size-factor   = float(default=1.0)
        hooks                   = boolean(default="yes")
        before-backup           = force_list(default=list())
        after-backup            = force_list(default=list())
        backup-failure          = force_list(default=list())
        """).splitlines())
    configspec = staticmethod(configspec)
