from typing import Callable, Dict, Optional, TypeVar, Union, overload

import anyio.abc
from typing_extensions import Literal, ParamSpec

from ..models import CommandInteraction
from .base import Callback
from .context import MessageCommand, UserCommand
from .option import CommandType
from .slash import Command, SubcommandGroup

__all__ = ('CommandRegistrar',)


P = ParamSpec('P')
RT = TypeVar('RT')
CommandUnion = Union[Command[P, RT], MessageCommand[P, RT], UserCommand[P, RT]]


class CommandRegistrar:
    """Root registrar of command handlers.

    Attributes:
        commands: A dictionary of all registered commands.
    """

    commands: Dict[str, Command]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.commands = {}

    async def invoke_command(self, interaction: CommandInteraction) -> None:
        """Handle the interaction and trigger appropriate callbacks.

        There is not much use of this method as a user unless this class
        is being extended.

        Parameters:
            interaction: The interaction to handle.
            tg: An anyio task group that will be used to launch callbacks.
        """
        command = self.commands.get(interaction.name)
        if command is None:
            return

        await command.invoke(interaction, interaction.options)

    def add_command(self, command: Command) -> None:
        """Register a command to be added to the internal dictionary.

        This should be used over manipulating the internal dictionary.

        Parameters:
            command: The command to register into the dictionary.
        """
        if command.name is None:
            raise ValueError('Command cannot be registered with no name')

        self.commands[command.name] = command

    def remove_command(self, command: Command) -> None:
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

        if self.commands.get(command.name) != command:
            raise ValueError(
                "'command' has not been registered previously or another"
                "command is registered in its place"
            )

        del self.commands[command.name]

    def group(
        self,
        *,
        name: str,
        description: str
    ) -> SubcommandGroup:
        """Register and create a slash command without a callback.

        This exist so that slash commands can be created without attaching a
        dummy-callback. Context menu commands cannot have subcommands, for that
        reason this will always return a slash command.

        Examples:

            ```python
            from wumpy import interactions

            app = interactions.InteractionApp(...)

            parent = app.group(name='hello', description='Greet and say hello')

            ...  # Register subcommands
            ```

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

        The decorator can be used both with and without the parentheses.

        Examples:
            ```python
            from wumpy.interactions import InteractionApp, CommandInteraction

            app = InteractionApp(...)

            @app.command()
            async def random(interaction: CommandInteraction) -> None:
                await interaction.respond('4')  # chosen by fair dice roll
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

            self.add_command(command)  # type: ignore
            return command

        if callable(type):
            return decorator(type)

        return decorator
