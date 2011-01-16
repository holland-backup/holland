class CommandError(Exception):
    """Base exception class for command errors"""

class CommandNotFoundError(CommandError):
    """Raised when a command could not be loaded"""

class CommandRuntimeError(CommandError):
    """Raised when an unexpected exception occurs when running a command"""
