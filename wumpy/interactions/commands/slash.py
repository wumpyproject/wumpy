import inspect
from functools import partial
from typing import (
    Any, Callable, Dict, List, Optional, TypeVar, Union, overload
)

import anyio.abc
from typing_extensions import ParamSpec

from ...errors import CommandNotFound, CommandSetupError
from ...utils import MISSING, _eval_annotations
from ..base import (
    ApplicationCommandOption, CommandInteraction, CommandInteractionOption
)
from .base import Callback, CommandCallback
from .option import CommandType, OptionClass

__all__ = ('Subcommand', 'SubcommandGroup', 'SlashCommand')


P = ParamSpec('P')
RT = TypeVar('RT')


class Subcommand(CommandCallback[P, RT]):
    """Subcommand and final callback handling an interaction.

    A subcommand cannot have another subcommand nested under it.

    Attributes:
        name: The name of the subcommand.
        description: A description of what the subcommand does.
        options: Options you can pass to the subcommand.
    """

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
        annotations = _eval_annotations(function)

        for param in signature.parameters.values():
            if (
                # issubclass() raises a TypeError if all arguments aren't types
                # and classes are all instances of 'type'
                isinstance(param.annotation, type) and
                issubclass(param.annotation, CommandInteraction)
            ):
                continue

            if isinstance(param.default, OptionClass):
                option = param.default
            else:
                option = OptionClass()

            # Make the option aware of the parameter it is defined in
            option.update(
                # The annotations dictionary may contain an evaluated version
                # of the annotation as opposed to a string or ForwardRef
                param.replace(
                    annotation=annotations.get(param.name, param.annotation)
                )
            )

            self.options[option.name] = option

        super()._set_callback(function)

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption],
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Handle an interaction and start the callback with the task group.

        Parameters:
            interaction: The interaction to handle.
            options: A list of options to resolve values from.
            tg: The task group to start the callback with.
        """

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
        choices: Union[
            List[Union[str, int, float]],
            Dict[str, Union[str, int, float]]
        ] = MISSING,
        min: int = MISSING,
        max: int = MISSING,
        type: ApplicationCommandOption = MISSING
    ) -> None:
        """Update values of a slash command's options.

        The values passed here will override any previously set values.

        Parameters:
            param: The parameter name to update.
            name: The new name of the option.
            description: The new description of the option.
            required: Whether the option can be omitted.
            choices: Strict set of choices that the user needs to pick from.
            min: Smallest number that can be entered for number types
            max: Biggest number that can be entered for number types
            type: New application command option type to use.

        Exceptions:
            ValueError: There's no parameter with the name passed.
        """
        # It is okay if this is O(n) to keep it O(1) when the app is running
        found = [option for option in self.options.values() if option.param == param]
        if not found:
            raise ValueError("Could not find parameter with name '{param}'")

        option = found[0]

        if name is not MISSING:
            # We have to update the internal dictionary where the option is
            # stored so that it can be found correctly when receiving an
            # interaction from Discord.
            del self.options[option.name]
            self.options[name] = option

        option._update_values(
            name=name, description=description, required=required,
            choices=choices, min=min, max=max, type=type
        )

    def to_dict(self) -> Dict[str, Any]:
        """Turn the subcommand into a payload to send to Discord."""
        return {
            **super().to_dict(),
            'description': self.description,
            'type': ApplicationCommandOption.subcommand.value,
            'options': [option.to_dict() for option in self.options.values()]
        }


class SubcommandGroup:
    """Subcommand group, which cannot in of itself be called.

    This follows the Discord API with how subcommand-groups can be used. With
    that reason you do not need a callback attached, and any options specified
    will not work.

    Attributes:
        name: The name of the subcommand group.
        description: Description of what the subcommand group does.
        commands: A dictionary of all registered subcommands.
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
        """Handle and forward the interaction to the correct subcommand.

        Parameters:
            interaction: The interaction to handle.
            options: Options to find the subcommand type in.
            tg: The task group to forward into the subcommand.

        Exceptions:
            CommandSetupError: Couldn't find the subcommand or there is none.
        """
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
        """Register a subcommand handler once it has been given a name.

        Parameters:
            command: The command to register into the internal dict.

        Exceptions:
            ValueError: The command is already registered.
        """
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
        """Create and register a subcommand of this group.

        This decorator can be used both with and without parentheses.

        Parameters:
            callback: This gets filled by the decorator.
            name: The name of the subcommand.
            description: The description of the subcommand.
        """
        def decorator(func: Callback[P, RT]) -> Subcommand[P, RT]:
            subcommand = Subcommand(func, name=name, description=description)
            self.register_command(subcommand)
            return subcommand

        if callable(callback):
            return decorator(callback)

        return decorator

    def to_dict(self) -> Dict[str, Any]:
        """Turn the subcommand group into a payload to send to Discord."""
        return {
            'name': self.name,
            'type': ApplicationCommandOption.subcommand_group.value,
            'description': self.description,
            'options': [option.to_dict() for option in self.commands.values()]
        }


class SlashCommand(Subcommand[P, RT]):
    """Top-level slash command which may contain other groups or subcommands.

    Attributes:
        name: The name of the slash command.
        description: The description of the command.
        commands: Internal dict of all registered subcommands and groups.
    """

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
        """Handle and forward the interaction to the correct subcommand.

        Parameters:
            interaction: The interaction to forward and handle.
            tg: The task group to start callbacks with.
        """
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
        """Register the subcommand, or subcommand group.

        Parameters:
            command: The command to register.

        Exceptions:
            ValueError: The command is already registered.
        """
        if command.name in self.commands:
            raise ValueError(f"Command with name '{command.name}' already registered")

        self.commands[command.name] = command

    def group(
        self,
        *,
        name: str,
        description: str,
    ) -> SubcommandGroup:
        """Create a subcommand group without a callback on this slash command.

        Examples:

            ```python
            from wumpy.interactions import InteractionApp, CommandInteraction

            app = InteractionApp(...)

            slash = app.group(name='gesture', description='Gesture something')

            group = app.group(name='hello', description='Hello :3')

            ...  # Register subcommands on this group
            ```

        Parameters:
            name: The name of the subcommand group.
            description: The description of the subcommand group.
        """
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
        """Create a subcommand directly on the slash command.

        Examples:

            ```python
            from wumpy.interactions import InteractionApp, CommandInteraction

            app = InteractionApp(...)

            slash = app.group(name='hello', description='👋 *waving*')

            @slash.command()
            async def world(interaction: CommandInteraction) -> None:
                await interaction.respond('Hello world')
            ```
            """
        def decorator(func: Callback[P, RT]) -> Subcommand[P, RT]:
            subcommand = Subcommand(func, name=name, description=description)
            self.register_command(subcommand)
            return subcommand

        if callable(callback):
            return decorator(callback)

        return decorator

    def to_dict(self) -> Dict[str, Any]:
        """Turn this slash command into a full payload to send to Discord."""
        return {
            'name': self.name,
            'type': CommandType.chat_input.value,
            'description': self.description,
            'options': [option.to_dict() for option in self.options.values()]
        }
