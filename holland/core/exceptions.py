"""
Standard public exceptions that are raised by
the various APIs in holland-core
"""

class ConfigError(Exception):
    """Configuration error"""

class InsufficientSpaceError(Exception):
    """Operation could not complete due to disk space"""

class ArgumentError(Exception):
    """Invalid argument"""
