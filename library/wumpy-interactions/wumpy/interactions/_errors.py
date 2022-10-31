__all__ = (
    'CommandSetupError',
)


class CommandSetupError(Exception):
    """Raised when local command setup does not align with interactions.

    Examples of this is incorrect types of local options compared to what
    Discord sends, or subcommand-groups not receiving subcommands.
    """
    pass
