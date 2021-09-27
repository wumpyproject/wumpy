import inspect
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

import anyio.abc

from ...errors import CommandNotFound, CommandSetupError
from ...utils import MISSING
from ..base import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption
)
from .base import CommandCallback
from .option import CommandType, OptionClass


class Subcommand(CommandCallback):
    """Subcommand and final callback handling an interaction."""

    name: str
    description: str

    options: Dict[str, OptionClass]

    __slots__ = ('description', 'options')

    def __init__(
        self,
        callback: Optional[Callable[..., Coroutine]] = None,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> None:
        self.description = description
        self.options = {}

        super().__init__(callback, name=name)

    def _set_callback(self, function: Callable[..., Coroutine]) -> None:
        doc = inspect.getdoc(function)
        if self.description is MISSING and doc is not None:
            # Similar to Markdown, we want to turn one full stop character into
            # space, and two characters into one.
            doc = doc.split('\n\n')[0].replace('\n', ' ')
            self.description = doc

        signature = inspect.signature(function)

        for param in signature.parameters.values():
            if isinstance(param.default, OptionClass):
                option = param.default
            else:
                option = OptionClass()

            # Make the option aware of the parameter it is defined in
            option.update(param)

            self.options[option.name] = option

        super()._set_callback(function)

    def update_option(
        self,
        param: str,
        *,
        name: str = MISSING,
        description: str = MISSING,
        required: bool = MISSING,
        choices: Dict[str, Union[str, int, float]] = MISSING,
        type: ApplicationCommandOption = MISSING
    ) -> None:
        """Update values of a slash command's options.

        The values passed here will override any previously set values.
        """
        # It is okay if this is O(n) to keep it O(1) when the app is running
        found = [option for option in self.options.values() if option.param == param]
        if not found:
            raise ValueError("Could not find parameter with name '{param}'")

        option = found[0]

        if type is not MISSING:
            option.type = type

        if name is not MISSING:
            option.name = name

        if description is not MISSING:
            option.description = description

        if required is not MISSING:
            option.required = required

        if choices is not MISSING:
            option.choices = choices

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            'description': self.description,
            'type': ApplicationCommandOption.subcommand,
            'options': [option.to_dict() for option in self.options.values()]
        }


class SubcommandGroup:
    """Subcommand group, which cannot in of itself be called.

    This follows the Discord API with how subcommand-groups can be used. With
    that reason you do not need a callback attached, and any options specified
    will not work.
    """

    name: str
    description: str

    subcommands: Dict[str, Subcommand]

    __slots__ = ('name', 'description', 'subcommands')

    def __init__(
        self,
        *,
        name: str,
        description: str
    ) -> None:
        self.name = name
        self.description = description

        self.subcommands = {}

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption],
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Handle and forward the interaction to the correct subcommand."""
        found = [option for option in options if option.type is ApplicationCommandOption.subcommand]
        if not found:
            raise CommandSetupError('Subcommand-group did not receive a subcommand option')

        command = self.subcommands.get(found[0].name)
        if not command:
            raise CommandSetupError(
                "Could not find subcommand '{found[0].name}' of '{self.name}'"
            )

        return command.handle_interaction(interaction, found[0].options, tg=tg)

    def register_command(self, command: Subcommand) -> None:
        """Register a subcommand handler once it has been given a name."""
        self.subcommands[command.name] = command

    def subcommand(
        self,
        callback: Callable[..., Coroutine] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> Subcommand:
        """Create a subcommand with this group as the parent.

        The subcommand is later registered once a name can be facilitated, be
        very, this may never happen if no name or callback is added.
        """
        subcommand = Subcommand(callback, name=name, description=description)

        self.subcommands[subcommand.name] = subcommand
        return subcommand

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': ApplicationCommandOption.subcommand_group,
            'description': self.description,
            'options': [option.to_dict() for option in self.subcommands.values()]
        }


class SlashCommand(Subcommand):
    """Top-level slash command which may contain other groups or subcommands."""

    subcommands: Dict[str, Union[Subcommand, SubcommandGroup]]

    def __init__(
        self,
        callback: Optional[Callable[..., Coroutine]] = None,
        *,
        name: str,
        description: str
    ) -> None:
        super().__init__(callback, name=name, description=description)

    @property
    def full_name(self) -> str:
        return self.name

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption],
        *,
        tg: anyio.abc.TaskGroup
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
            return super().handle_interaction(interaction, options, tg=tg)

        # If we got here we should have found a subcommand option

        command = self.subcommands.get(option.name)
        if not command:
            raise CommandNotFound(interaction, f'{self.full_name} {command}')

        return command.handle_interaction(interaction, option.options, tg=tg)

    def register_command(self, command: Union[Subcommand, SubcommandGroup]) -> None:
        """Register the subcommand, or subcommand group."""
        self.subcommands[command.name] = command

    def group(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> SubcommandGroup:
        """Create a SubcommandGroup with this command as the parent.

        It is then registered once a name can be facilitated.
        """
        subcommand = SubcommandGroup(name=name, description=description)

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
        subcommand = Subcommand(callback, name=name, description=description)

        self.subcommands[subcommand.name] = subcommand
        return subcommand

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': CommandType.chat_input,
            'description': self.description,
            'options': [option.to_dict() for option in self.options.values()]
        }
