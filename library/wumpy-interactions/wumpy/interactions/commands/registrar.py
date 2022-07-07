from typing import Any, Callable, Dict, Optional, TypeVar, Union, overload

from typing_extensions import Literal, ParamSpec

from ..models import CommandInteraction
from .base import Callback
from .context import MessageCommand, UserCommand
from .option import CommandType
from .slash import Command, SubcommandGroup

__all__ = ['group', 'command', 'CommandRegistrar']


P = ParamSpec('P')
RT = TypeVar('RT', covariant=True)
CommandUnion = Union[
    Command[P, RT], MessageCommand[P, RT],
    UserCommand[P, RT], SubcommandGroup
]


def group(
    *,
    name: str,
    description: str
) -> SubcommandGroup:
    """Independently create a slash command group without a callback.

    This exist so that slash commands can be created without attaching a
    dummy-callback. Context menu commands cannot have subcommands, therefore
    this will always return a slash command.

    After using this decorator on a callback, you will need to register the
    command with the registrar. This is useful for defining a command in a
    different file than the main app.

    Examples:

        ```python
        from wumpy import interactions

        parent = interactions.group(
            name='hello',
            description='Greet and say hello'
        )

        ...  # Register subcommands
        ```

    Parameters:
        name: The name of the command.
        description: The description of the command.

    Returns:
        A subcommand group that can have subcommands added to it. You will need
        to register it with the registrar later on.
    """
    return SubcommandGroup(name=name, description=description)


@overload
def command(
    type: Callback[P, RT]
) -> Command[P, RT]:
    ...


@overload
def command(
    type: CommandType = CommandType.chat_input,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Callable[[Callback[P, RT]], Command[P, RT]]:
    ...


@overload
def command(
    type: Literal[CommandType.message],
    *,
    name: Optional[str] = None
) -> Callable[[Callback[P, RT]], MessageCommand[P, RT]]:
    ...


@overload
def command(
    type: Literal[CommandType.user],
    *,
    name: Optional[str] = None
) -> Callable[[Callback[P, RT]], UserCommand[P, RT]]:
    ...


def command(
    type: Union[CommandType, Callback[P, RT]] = CommandType.chat_input,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Union[CommandUnion[P, RT], Callable[[Callback[P, RT]], CommandUnion[P, RT]]]:
    """Independently create a command from a callback.

    After using this decorator on a callback, you will need to register the
    command with the registrar. This is useful for defining a command in a
    different file than the main app.

    The decorator can be used both with and without the parentheses.

    Examples:

        ```python
        from wumpy import interactions

        @interactions.command()
        async def random(interaction: interactions.CommandInteraction) -> None:
            await interaction.respond('4')  # Chosen by fair dice roll

        # Import the random command and register it on your app:
        from wumpy.interactions import InteractionApp

        from .other import random

        app = InteractionApp(...)
        app.add_command(random)
        ```

    Parameters:
        type: The type of the command. Defaults to a slash command.
        name: The name of the command.
        description: The description of the command.

    Returns:
        A command or function that returns a command. Depending on whether
        the decorator was used with or without parentheses.

    Exceptions:
        ValueError: The type wasn't a CommandType value
    """
    def decorator(func: Callback[P, RT]) -> CommandUnion[P, RT]:
        if type is CommandType.chat_input:
            command = Command(func, name=name, description=description)
        elif type is CommandType.message:
            command = MessageCommand(func, name=name)
        elif type is CommandType.user:
            command = UserCommand(func, name=name)
        else:
            raise ValueError("Unknown value of 'type':", type)

        return command

    if callable(type):
        return decorator(type)

    return decorator


class CommandRegistrar:
    """Root registrar of command handlers."""

    _commands: Dict[str, 'CommandUnion[..., object]']

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._commands = {}

    async def invoke_command(self, interaction: CommandInteraction) -> None:
        """Handle the interaction and trigger appropriate callbacks.

        There is not much use of this method as a user unless this class
        is being extended.

        Parameters:
            interaction: The interaction to handle.
            tg: An anyio task group that will be used to launch callbacks.
        """
        command = self._commands.get(interaction.name)
        if command is None:
            return

        await command.invoke(interaction, interaction.options)

    def add_command(self, command: 'CommandUnion[..., object]') -> None:
        """Register a command to be added to the internal dictionary.

        This should be used over manipulating the internal dictionary.

        Parameters:
            command: The command to register into the dictionary.
        """
        if command.name is None:
            raise ValueError('Command cannot be registered with no name')

        self._commands[command.name] = command

    def get_command(self, name: str) -> Optional['CommandUnion[..., object]']:
        """Get a registered command from the registrar.

        Parameters:
            name: The name of the command to lookup.

        Returns:
            The command if found, otherwise `None`.
        """
        return self._commands.get(name)

    def remove_command(self, command: 'CommandUnion[..., object]') -> None:
        """Unregister a command from the internal dictionary.

        This will raise a ValueError if the command passed isn't loaded where
        it is supposed to or if it was never registered in the first place.

        Parameters:
            command: The command to unregister from the dictionary.

        Raises:
            ValueError: The command couldn't be found where it's supposed to
        """
        if command.name is None:
            raise ValueError("Cannot unregister a command with no name")

        if self._commands.get(command.name) != command:
            raise ValueError(
                "'command' has not been registered previously or another"
                "command is registered in its place"
            )

        del self._commands[command.name]

    def group(
        self,
        *,
        name: str,
        description: str
    ) -> SubcommandGroup:
        """Register and create a slash command group without a callback.

        This is similar to `interactions.group()`, except that it automatically
        registers the command at the same time.

        Parameters:
            name: The name of the command.
            description: The description of the command.

        Returns:
            A registered subcommand group.
        """
        command = SubcommandGroup(name=name, description=description)
        self.add_command(command)  # type: ignore
        return command

    @overload
    def command(
        self,
        type: Callback[P, RT]
    ) -> Command[P, RT]:
        ...

    @overload
    def command(
        self,
        type: CommandType = CommandType.chat_input,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], Command[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.message],
        *,
        name: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], MessageCommand[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.user],
        *,
        name: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], UserCommand[P, RT]]:
        ...

    def command(
        self,
        type: Union[CommandType, Callback[P, RT]] = CommandType.chat_input,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Union[CommandUnion[P, RT], Callable[[Callback[P, RT]], CommandUnion[P, RT]]]:
        """Register and create a new application command through a decorator.

        This is similar to the `@interactions.command()` decorator, except that
        it automatically registers the command at the same time.

        Parameters:
            type: The type of the command. Defaults to a slash command.
            name: The name of the command.
            description: The description of the command.

        Returns:
            A command or function that returns a command. Depending on whether
            the decorator was used with or without parentheses.

        Exceptions:
            ValueError: The type wasn't a CommandType value
        """
        def decorator(func: Callback[P, RT]) -> CommandUnion[P, RT]:
            if type is CommandType.chat_input:
                command = Command(func, name=name, description=description)
            elif type is CommandType.message:
                command = MessageCommand(func, name=name)
            elif type is CommandType.user:
                command = UserCommand(func, name=name)
            else:
                raise ValueError("Unknown value of 'type':", type)

            self.add_command(command)  # type: ignore
            return command

        if callable(type):
            return decorator(type)

        return decorator
