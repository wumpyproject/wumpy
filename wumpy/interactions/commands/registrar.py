from typing import Any, Callable, Dict

from ...utils import MISSING
from .slash import SlashCommand


class CommandRegistrar:
    """Root registrar of command handlers."""

    commands: Dict[str, SlashCommand]

    def __init__(self) -> None:
        self.commands = {}

    async def handle_interaction(self, send, interaction) -> None:
        """Handle the interaction, propogating it to the correct command handler."""
        command = self.commands.get(interaction.name)
        if command is None:
            await send({'type': 'http.response.start', 'status': 404})
            await send({'type': 'http.response.body', 'body': b'Not Found'})
            return

        await command.handle_interaction(interaction, interaction.options)

    def register_command(self, command) -> None:
        """Register a command handler, the command must have a name."""
        if command.name is MISSING:
            raise RuntimeError('Cannot register a command with a MISSING name')

        self.commands[command.name] = command

    def command(
        self,
        callback: Callable[..., Any] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> SlashCommand:
        """Lazily create a new command.

        The command is later registered once the command gets a name, which may
        happen after the call of this function through a decorator. The command
        may never be registered if a name cannot be facilitated. Examples of
        this is creating a command without a name and assigning it to a variable.
        """
        return SlashCommand(callback, name=name, description=description, parent=self)
