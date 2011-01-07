"""Holland core API"""

from holland.core.plugin import load_plugin, iterate_plugins
from holland.core.spool import BackupSpool, BackupStore, SpoolError
from holland.core.backup import BackupManager, BackupPlugin, BackupJob, \
                                BackupError
