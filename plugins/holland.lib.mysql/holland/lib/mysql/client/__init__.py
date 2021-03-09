"""
Handle connections to MySQL
"""

from holland.lib.mysql.client.base import (
    AutoMySQLClient,
    MySQLClient,
    MySQLError,
    OperationalError,
    ProgrammingError,
    connect,
)

__all__ = [
    "connect",
    "MySQLClient",
    "AutoMySQLClient",
    "MySQLError",
    "ProgrammingError",
    "OperationalError",
]
