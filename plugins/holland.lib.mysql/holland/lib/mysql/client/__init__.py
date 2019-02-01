"""
Handle connections to MySQL
"""

from holland.lib.mysql.client.base import (
    MySQLClient,
    MySQLError,
    ProgrammingError,
    OperationalError,
    connect,
    AutoMySQLClient,
)

__all__ = [
    "connect",
    "MySQLClient",
    "AutoMySQLClient",
    "MySQLError",
    "ProgrammingError",
    "OperationalError",
]
