import inspect
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, overload

import anyio.abc
from typing_extensions import ParamSpec

from ...errors import CommandNotFound, CommandSetupError
from ...utils import MISSING
from ..base import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption
)
from .base import CommandCallback, Callback
from .option import CommandType, OptionClass

P = ParamSpec('P')
RT = TypeVar('RT')


class Subcommand(CommandCallback[P, RT]):
    """Subcommand and final callback handling an interaction."""

    name: str
    description: str

    options: Dict[str, OptionClass]

    __slots__ = ('description', 'options')

    def __init__(
        self,
        callback: Optional[Callback[P, RT]] = None,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> None:
        self.description = description
        self.options = {}

        super().__init__(callback, name=name)

    def _set_callback(self, function: Callback[P, RT]) -> None:
        doc = inspect.getdoc(function)
        if self.description is MISSING and doc is not None:
            # Similar to Markdown, we want to turn one full stop character into
            # space, and two characters into one.
            doc = doc.split('\n\n')[0].replace('\n', ' ')
            self.description = doc

        signature = inspect.signature(function)

        for param in signature.parameters.values():
            print(param.annotation)
            if issubclass(param.annotation, CommandInteraction):
                continue

            if isinstance(param.default, OptionClass):
                option = param.default
            else:
                option = OptionClass()

            # Make the option aware of the parameter it is defined in
            option.update(param)

            self.options[option.name] = option

        super()._set_callback(function)

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption],
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        # We receive options as a JSON array but this is inefficient to lookup
        mapping = {option.name: option for option in options}
        args, kwargs = [], {}

        for option in self.options.values():
            data = mapping.get(option.name)
            if option.kind in {option.kind.POSITIONAL_ONLY, option.kind.POSITIONAL_OR_KEYWORD}:
                args.append(option.resolve(interaction, data))
            else:
                kwargs[option.param] = option.resolve(interaction, data)

        tg.start_soon(partial(self._call_wrapped, interaction, *args, **kwargs))

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

    commands: Dict[str, Subcommand]

    __slots__ = ('name', 'description', 'commands')

    def __init__(
        self,
        *,
        name: str,
        description: str
    ) -> None:
        self.name = name
        self.description = description

        self.commands = {}

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

        command = self.commands.get(found[0].name)
        if not command:
            raise CommandSetupError(
                "Could not find subcommand '{found[0].name}' of '{self.name}'"
            )

        return command.handle_interaction(interaction, found[0].options, tg=tg)

    def register_command(self, command: Subcommand) -> None:
        """Register a subcommand handler once it has been given a name."""
        if command.name in self.commands:
            raise ValueError(f"Command with name '{command.name}' already registered")

        self.commands[command.name] = command

    @overload
    def command(self, callback: Callback[P, RT]) -> Subcommand[P, RT]:
        ...

    @overload
    def command(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callback[P, RT]], Subcommand[P, RT]]:
        ...

    def command(
        self,
        callback: Callback[P, RT] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> Union[Subcommand[P, RT], Callable[[Callback[P, RT]], Subcommand[P, RT]]]:
        """Create a subcommand with this group as the parent."""
        def decorator(func: Callback[P, RT]) -> Subcommand[P, RT]:
            subcommand = Subcommand(func, name=name, description=description)
            self.register_command(subcommand)
            return subcommand

        if callable(callback):
            return decorator(callback)

        return decorator

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': ApplicationCommandOption.subcommand_group,
            'description': self.description,
            'options': [option.to_dict() for option in self.commands.values()]
        }


class SlashCommand(Subcommand[P, RT]):
    """Top-level slash command which may contain other groups or subcommands."""

    commands: Dict[str, Union[Subcommand, SubcommandGroup]]

    def __init__(
        self,
        callback: Optional[Callback[P, RT]] = None,
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
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Handle and forward the interaction to the correct subcommand."""
        for option in interaction.options:
            if option.type in {
                    ApplicationCommandOption.subcommand,
                    ApplicationCommandOption.subcommand_group
            }:
                break
        else:
            # There's no subcommand, or subcommand group option. We should
            # handle the interaction ourselves.
            return super().handle_interaction(interaction, interaction.options, tg=tg)

        # If we got here we should have found a subcommand option

        command = self.commands.get(option.name)
        if not command:
            raise CommandNotFound(interaction, f'{self.full_name} {command}')

        return command.handle_interaction(interaction, option.options, tg=tg)

    def register_command(self, command: Union[Subcommand, SubcommandGroup]) -> None:
        """Register the subcommand, or subcommand group."""
        if command.name in self.commands:
            raise ValueError(f"Command with name '{command.name}' already registered")

        self.commands[command.name] = command

    def group(
        self,
        *,
        name: str,
        description: str,
    ) -> SubcommandGroup:
        """Create a SubcommandGroup with this command as the parent."""
        group = SubcommandGroup(name=name, description=description)
        self.register_command(group)
        return group

    @overload
    def command(self, callback: Callback[P, RT]) -> Subcommand[P, RT]:
        ...

    @overload
    def command(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Callable[[Callback[P, RT]], Subcommand[P, RT]]:
        ...

    def command(
        self,
        callback: Callback[P, RT] = MISSING,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Union[Subcommand[P, RT], Callable[[Callback[P, RT]], Subcommand[P, RT]]]:
        """Create a Subcommand with this slash command as the parent."""
        def decorator(func: Callback[P, RT]) -> Subcommand[P, RT]:
            subcommand = Subcommand(func, name=name, description=description)
            self.register_command(subcommand)
            return subcommand

        if callable(callback):
            return decorator(callback)

        return decorator

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': CommandType.chat_input,
            'description': self.description,
            'options': [option.to_dict() for option in self.options.values()]
        }
