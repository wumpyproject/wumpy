from typing import Callable, Coroutine, Dict, Literal, Union, overload

from ...utils import MISSING
from .context import ContextMenuCommand, MessageCommand, UserCommand
from .option import CommandType
from .slash import SlashCommand


class CommandRegistrar:
    """Root registrar of command handlers."""

    commands: Dict[str, SlashCommand]

    full_name = ''

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.commands = {}

    def handle_command(self, interaction, *, tg) -> None:
        """Handle the interaction, propogating it to the correct command handler."""
        command = self.commands.get(interaction.name)
        if command is None:
            return

        command.handle_interaction(interaction, interaction.options, tg=tg)

    def register_command(self, command) -> None:
        """Register a command handler, the command must have a name."""
        if command.name is MISSING:
            raise ValueError('Cannot register a command with a missing name')

        self.commands[command.name] = command

    def group(
        self,
        *,
        name: str,
        description: str
    ) -> SlashCommand:
        """Create a slash command without a callback.

        This exist so that slash commands can be created without attaching a
        dummy-callback. Context menu commands cannot have subcommands, for that
        reason this will always return a slash command.

        Example usage:

        ```python
        from wumpy import interactions

        app = interactions.InteractionApp(...)

        parent = app.group(name='hello', description='Greet and say hello')

        ...  # Register subcommands
        ```
        """
        return SlashCommand(name=name, description=description)

    @overload
    def command(
        self,
        type: CommandType = CommandType.chat_input,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callable[..., Coroutine]], SlashCommand]:
        ...

    @overload
    def command(
        self,
        type: Literal[CommandType.user, CommandType.message],
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callable[..., Coroutine]], ContextMenuCommand]:
        ...

    def command(
        self,
        type: CommandType = CommandType.chat_input,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callable[..., Coroutine]], Union[SlashCommand, ContextMenuCommand]]:
        """Register and create a new application command through a decorator.

        Example usage:

        ```python
        from wumpy import interactions

        app = interactions.InteractionApp(...)

        @app.command()
        async def random(interaction: interactions.CommandInteraction) -> None:
            await interaction.respond('4')  # chosen by fair dice roll
        ```
        """
        def decorator(func: Callable[..., Coroutine]) -> Union[SlashCommand, ContextMenuCommand]:
            if type is CommandType.chat_input:
                return SlashCommand(func, name=name, description=description)
            elif type is CommandType.message:
                return MessageCommand(func, name=name)
            elif type is CommandType.user:
                return UserCommand(func, name=name)
            else:
                raise ValueError("Unknown value of 'type':", type)

        return decorator
