import inspect
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List, Union

from ...utils import MISSING
from ..base import ApplicationCommandOption, CommandInteraction, CommandInteractionOption
from .base import CommandCallback

if TYPE_CHECKING:
    from .registrar import CommandRegistrar


class Subcommand(CommandCallback):
    """Subcommand and final callback handling an interaction."""

    name: str
    description: str

    parent: Union['SubcommandGroup', 'SlashCommand', 'CommandRegistrar', None]

    def __init__(
        self,
        callback: Callable[..., Awaitable[None]] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
        parent: Union['SubcommandGroup', 'SlashCommand', 'CommandRegistrar', None] = None
    ) -> None:
        self.name = name
        self.description = description

        self.parent = parent

        # We need to call super()s __init__ last because it calls the
        # _set_callback method, and that shouldn't be done before we at least
        # set self.name and self.description to MISSING
        super().__init__(callback)

    def _set_callback(self, function) -> None:
        self.name = function.__name__ if self.name is MISSING else self.name

        doc = inspect.getdoc(function)
        if self.description is MISSING and doc is not None:
            # Similar to Markdown, we want to turn one full stop character into
            # space, and two characters into one.
            doc = doc.split('\n\n')[0].replace('\n', ' ')
            self.description = doc

        super()._set_callback(function)

        if self.parent:
            self.parent.register_command(self)


class SubcommandGroup(Subcommand):
    """Subcommand group, which cannot in of itself be called.

    This follows the Discord API with how subcommand-groups can be used. With
    that reason you do not need a callback attached, and any options specified
    will not work.
    """

    name: str
    description: str

    parent: 'SlashCommand'
    subcommands: Dict[str, Subcommand]

    def __init__(
        self,
        callback: Callable[..., Awaitable[None]] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
        parent: 'SlashCommand'
    ) -> None:
        super().__init__(callback, name=name, description=description, parent=parent)

        self.subcommands = {}

    async def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        """Handle and forward the interaction to the correct subcommand."""
        for option in options:
            if option.type is ApplicationCommandOption.subcommand:
                break
        else:
            raise RuntimeError('SubcommandGroup cannot handle interaction')

        # If we got here we should have found a subcommand option

        command = self.subcommands.get(option.name)
        if not command:
            raise RuntimeError('Could not find command locally')

        # Primarily for static type checkers, but it's also a good santity check
        assert option.options is not None, 'Subcommand option missing further options'

        return await command.handle_interaction(interaction, option.options)

    def register_command(self, command: Subcommand) -> None:
        """Register a subcommand handler once it has been given a name."""
        if command.name is MISSING:
            raise RuntimeError('Cannot register a command with a MISSING name')

        self.subcommands[command.name] = command

    def subcommand(
        self,
        callback: Callable[..., Awaitable[None]] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> Subcommand:
        """Create a subcommand with this group as the parent.

        The subcommand is later registered once a name can be facilitated, be
        very, this may never happen if no name or callback is added.
        """
        subcommand = Subcommand(callback, name=name, description=description, parent=self)

        self.subcommands[subcommand.name] = subcommand
        return subcommand


class SlashCommand(Subcommand):
    """Top-level slash command which may contain other groups or subcommands."""

    subcommands: Dict[str, Union[Subcommand, SubcommandGroup]]

    def __init__(
        self,
        callback,
        *,
        name: str,
        description: str,
        parent: 'CommandRegistrar'
    ) -> None:
        super().__init__(callback, name=name, description=description, parent=parent)

    async def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        """Handle and forward the interaction to the correct subcommand."""
        for option in options:
            if option.type in {
                    ApplicationCommandOption.subcommand,
                    ApplicationCommandOption.subcommand_group
            }:
                break
        else:
            # There's no subcommand, or subcommand group option. We should
            # handle the interaction ourselves.
            return await super().handle_interaction(interaction, options)

        # If we got here we should have found a subcommand option

        command = self.subcommands.get(option.name)
        if not command:
            raise RuntimeError("Could not find command locally")

        assert option.options is not None, 'Subcommand option missing further options'

        return await command.handle_interaction(interaction, option.options)

    def register_command(self, command: Union[Subcommand, SubcommandGroup]) -> None:
        """Register the subcommand, or subcommand group."""
        # This is called afterhand, when the command is given a name
        if command.name is MISSING:
            raise RuntimeError('Cannot register a command with a MISSING name')

        self.subcommands[command.name] = command

    def group(
        self,
        callback: Callable[..., Any] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> SubcommandGroup:
        """Create a SubcommandGroup with this command as the parent.

        It is then registered once a name can be facilitated.
        """
        subcommand = SubcommandGroup(callback, name=name, description=description, parent=self)

        if subcommand.name is not MISSING:
            self.subcommands[subcommand.name] = subcommand
        return subcommand

    def subcommand(
        self,
        callback: Callable[..., Any] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Subcommand:
        """Create a Subcommand with this slash command as the parent.

        The subcommand may never be registered if no name can be facilitated,
        to ensure this never happens make sure to always register a callback
        or explicitly define a name.
        """
        subcommand = Subcommand(callback, name=name, description=description, parent=self)

        if subcommand.name is not MISSING:
            self.subcommands[subcommand.name] = subcommand
        return subcommand
