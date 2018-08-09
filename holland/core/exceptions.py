"""
Standard public exceptions that are raised by
the various APIs in holland-core
"""

class ConfigError(Exception):
    """Configuration error"""
    pass

class InsufficientSpaceError(Exception):
    """Operation could not complete due to disk space"""
    pass

class ArgumentError(Exception):
    """Invalid argument"""
