# coding: utf-8
"""
holland.backup.delphini.error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exceptions classes used by delphini

:copyright: 2010-2011 by Andrew Garner
:license: BSD, see LICENSE.rst for details
"""

class ClusterError(Exception):
    """Base exception raised when error is encountered during a cluster
    backup"""

class ClusterCommandError(ClusterError):
    """Raised when running a command during a cluster backup"""
    def __init__(self, message, status):
        ClusterError.__init__(self, message)
        self.message = message
        self.status = status
