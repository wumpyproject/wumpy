__all__ = (
    'WumpyException',
    'ExtensionFailure',
)


class WumpyException(Exception):
    """Base exception that all other exceptions from the library subclass."""
    pass


class ConnectionClosed(WumpyException):
    """Exception raised when the WebSocket to the Discord gateway was closed."""
    pass


class CommandException(WumpyException):
    """Parent for all exceptions raised regarding command handlers."""
    pass


class ExtensionFailure(WumpyException):
    """Exception related to loading or unloading of extensions."""
    pass
