"""
    holland.core.backup
    ~~~~~~~~~~~~~~~~~~~

    Holland Backup API

    :copyright: 2010-2011 Rackspace US, Inc.
    :license: BSD, see LICENSE.rst for details
"""

from holland.core.backup.error import BackupError
from holland.core.backup.plugin import BackupPlugin
from holland.core.backup.manager import BackupManager
from holland.core.backup.spool import BackupSpool, BackupStore

__all__ = [
    'BackupPlugin',
    'BackupError',
    'BackupManager',
    'BackupSpool',
    'BackupStore',
]
