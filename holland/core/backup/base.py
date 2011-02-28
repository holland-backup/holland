"""Standard Holland Backup API classes"""

import logging
from textwrap import dedent
from holland.core.plugin import ConfigurablePlugin
from holland.core.config import Configspec

LOG = logging.getLogger(__name__)

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

class BackupPlugin(ConfigurablePlugin):
    """Interface that Holland Backup Plugins should conform to"""

    #: BackupStore instance provides via the setup() method
    store = None

    def setup(self, backupstore):
        """Setup the backup directory

        A ``BackupStore`` instance is provided to the plugin whose
        ``path`` instance points to the directory where backup files
        should be stored.
        """
        self.store = backupstore

    def pre(self):
        """Run before starting a backup"""

    def estimate(self):
        """Estimate the size of the backup this plugin would produce"""
        return 0

    def backup(self):
        """Backup to the specified path"""

    def dryrun(self):
        """Perform a dry-run backup to the specified path"""

    def post(self):
        """Run after a backup"""

    def release(self):
        """Release resources held by this plugin

        If a backup plugin uses some resource as part of the backup
        process this method give it a chance to free that resource.
        This will be called prior to the backupstore being purged
        during a purge operation or as part an explicit release
        request as long as the backupstore plugin is loadable.

        This method does nothing by default and generally does not
        need to be overriden.  This exists primarily for snapshot
        style plugins that may create a snapshot as the primary means
        of backup and sometime later will be requested to release that
        snapshot.
        """

    #@classmethod
    def configspec(cls):
        """Provide standard backup configspec

        :returns: Configspec instance
        """
        return Configspec.parse(dedent("""
        [holland:backup]
        plugin                  = string
        auto-purge-failures     = boolean(default=yes)
        purge-policy            = option("manual",
                                         "before-backup",
                                         "after-backup",
                                         default="after-backup")
        backups-to-keep         = integer(default=1, aliasof="retention-count")
        retention-count         = integer(default=1)
        estimated-size-factor   = float(default=1.0)
        estimation-method       = string(default="plugin")
        hooks                   = list(default=list())
        """).splitlines())
    configspec = classmethod(configspec)
