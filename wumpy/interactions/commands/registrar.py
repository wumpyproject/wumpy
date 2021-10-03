from typing import Callable, Dict, Literal, TypeVar, Union, overload

import anyio.abc
from typing_extensions import ParamSpec

from ...utils import MISSING
from ..base import CommandInteraction
from .base import Callback
from .context import MessageCommand, UserCommand
from .option import CommandType
from .slash import SlashCommand

__all__ = ('CommandRegistrar',)


P = ParamSpec('P')
RT = TypeVar('RT')
Command = Union[SlashCommand[P, RT], MessageCommand[P, RT], UserCommand[P, RT]]


class CommandRegistrar:
    """Root registrar of command handlers.

    Attributes:
        commands: A dictionary of all registered commands.
    """

    commands: Dict[str, Command]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.commands = {}

    def handle_command(
        self,
        interaction: CommandInteraction,
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
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

        command.handle_interaction(interaction, tg=tg)

    def register_command(self, command: Command) -> None:
        """Register a command to be added to the internal dictionary.

        This should be used over manipulating the internal dictionary.

        Parameters:
            command: The command to register into the dictionary.
        """
        self.commands[command.name] = command

    def group(
        self,
        *,
        name: str,
        description: str
    ) -> SlashCommand:
        """Register and create a slash command without a callback.

        This exist so that slash commands can be created without attaching a
        dummy-callback. Context menu commands cannot have subcommands, for that
        reason this will always return a slash command.

        **Usage:**
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
            A registered new Slashcommand without a callback.
        """
        command = SlashCommand(name=name, description=description)
        self.register_command(command)  # type: ignore
        return command

    @overload
    def command(
        self,
        type: Callback[P, RT]
    ) -> SlashCommand[P, RT]:
        ...

    @overload
    def command(
        self,
        type: CommandType = CommandType.chat_input,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callback[P, RT]], SlashCommand[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.message],
        *,
        name: str = MISSING
    ) -> Callable[[Callback[P, RT]], MessageCommand[P, RT]]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.user],
        *,
        name: str = MISSING
    ) -> Callable[[Callback[P, RT]], UserCommand[P, RT]]:
        ...

    def command(
        self,
        type: Union[CommandType, Callback[P, RT]] = CommandType.chat_input,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Union[Command[P, RT], Callable[[Callback[P, RT]], Command[P, RT]]]:
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
        def decorator(func: Callback[P, RT]) -> Command[P, RT]:
            if type is CommandType.chat_input:
                command = SlashCommand(func, name=name, description=description)
            elif type is CommandType.message:
                command = MessageCommand(func, name=name)
            elif type is CommandType.user:
                command = UserCommand(func, name=name)
            else:
                raise ValueError("Unknown value of 'type':", type)

            self.register_command(command)  # type: ignore
            return command

        if callable(type):
            return decorator(type)

        return decorator
