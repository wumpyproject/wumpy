__all__ = (
    'WumpyException', 'ExtensionFailure'
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


class CommandSetupError(CommandException):
    """Raised when local command setup does not align with interactions.

    Examples of this is incorrect types of local options compared to what
    Discord sends, or subcommand-groups not receiving subcommands.
    """
    pass


class ExtensionFailure(WumpyException):
    """Exception related to loading or unloading of extensions."""
    pass
