import inspect
from asyncio import iscoroutinefunction
from typing import (
    Any, Callable, Dict, List, Optional, OrderedDict, TypeVar, Union, overload
)

from discord_typings import (
    ApplicationCommandOptionData, ApplicationCommandPayload
)
from typing_extensions import ParamSpec
from wumpy.models import ApplicationCommandOption, CommandInteractionOption

from ..models import CommandInteraction
from .base import Callback, CommandCallback
from .middleware import CommandMiddlewareMixin
from .option import OptionClass

__all__ = ('Command', 'SubcommandGroup', 'command_payload')


P = ParamSpec('P')
RT = TypeVar('RT')


class Command(CommandMiddlewareMixin, CommandCallback[P, RT]):
    """Command with a callback for its handling.

    Commands function as subcommands and cannot have other subcommands nested
    under them.
    """

    name: Optional[str]
    description: Optional[str]
    options: 'OrderedDict[str, OptionClass]'

    def __init__(
        self,
        callback: Callback[P, RT],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional['OrderedDict[str, OptionClass]'] = None
    ) -> None:
        self.name = name
        self.description = description

        self.options = options or OrderedDict()

        # __init__() will dispatch the processing methods below which means
        # that we need to set the attributes above first.
        super().__init__(callback)

    async def _inner_call(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> RT:
        # We receive options as a JSON array but this is inefficient to lookup
        mapping = {option.name: option for option in options}
        args, kwargs = [], {}

        for option in self.options.values():
            assert option.name is not None and option.kind is not None

            data = mapping.get(option.name)
            if option.kind in {option.kind.POSITIONAL_ONLY, option.kind.POSITIONAL_OR_KEYWORD}:
                args.append(option.resolve(interaction, data))
            else:
                kwargs[option.param] = option.resolve(interaction, data)

        return await self.callback(*args, **kwargs)

    def _process_callback(self, callback: Callback[P, RT]) -> None:
        if self.name is None:
            self.name = getattr(callback, '__name__', None)

        doc = inspect.getdoc(callback)
        if self.description is None and doc is not None:
            paragraps = doc.split('\n\n')
            if paragraps:
                # Similar to Markdown, we want to turn one newline character into
                # spaces, and two characters into one.
                self.description = paragraps[0].replace('\n', ' ')

        if not iscoroutinefunction(callback):
            raise TypeError("'callback' must be an 'async def' function")

        return super()._process_callback(callback)

    def _process_param(self, index: int, param: inspect.Parameter) -> None:
        if index == 0:
            if param.annotation is not param.empty:
                # If this is the first parameter, we need to make sure it is
                # either not annotated at all or its set as the interaction
                if (
                    isinstance(param.annotation, type)
                    and not issubclass(param.annotation, CommandInteraction)
                ):
                    raise TypeError(
                        "The first paramer of 'callback' cannot be annotated with "
                        "anything other than 'CommandInteraction'"
                    )

            return  # The interaction shouldn't be added to self.options

        if isinstance(param.default, OptionClass):
            option = param.default
        else:
            option = OptionClass(param.default)

        option.update(param)

        if option.name is None:
            raise ValueError('Cannot register unnamed option')

        self.options[option.name] = option

    def _process_no_params(self, signature: inspect.Signature) -> None:
        raise TypeError("'callback' has to have two parameters")

    def _process_return_type(self, annotation: Any) -> None:
        # We don't actually care about the return type, this is simply the last
        # method to be called when processing which we take advantage of.
        super()._process_return_type(annotation)

        defaults: List[Any] = []
        kw_defaults: Dict[str, Any] = {}

        pos_default = False

        for option in self.options.values():
            # Shouldn't be possible because we call update() inside
            # _process_param() above, which is where these are set.
            assert option.kind is not None and option.param is not None

            if option.kind in {option.kind.POSITIONAL_ONLY, option.kind.POSITIONAL_OR_KEYWORD}:
                if not option.has_default and pos_default:
                    raise TypeError('option without default follows option with default')

                if option.has_default:
                    pos_default = True
                    defaults.append(option.default)
            else:
                # We don't need to check for non-defaulted keyword-only
                # parameters following defaulted keyword-only parameters
                # because that would normally be allowed by Python syntax.
                if option.has_default:
                    kw_defaults[option.param] = option.default

        self.callback.__defaults__ = tuple(defaults)
        self.callback.__kwdefaults__ = kw_defaults

    def update_option(
        self,
        option: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        choices: Union[
            List[Union[str, int, float]],
            Dict[str, Union[str, int, float]],
            None
        ] = None,
        min: Optional[int] = None,
        max: Optional[int] = None,
        type: Optional[ApplicationCommandOption] = None
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
            ValueError: There's no option with the name passed.
        """
        found = self.options.get(option)
        if not found:
            raise ValueError(f"Could not find option with name '{option}'")

        if name is not None:
            # We have to update the internal dictionary where the option is
            # stored so that it can be found correctly when receiving an
            # interaction from Discord.
            assert found.name is not None
            del self.options[found.name]
            self.options[name] = found

        found._update_values(
            name=name, description=description, required=required,
            choices=choices, min=min, max=max, type=type
        )


class SubcommandGroup(CommandMiddlewareMixin):
    """Group of subcommands forwarding interactions.

    Subcommand groups has other subcommand under them but they cannot be called
    on their own.
    """

    name: str
    description: Optional[str]

    commands: Dict[str, Union['SubcommandGroup', Command]]

    def __init__(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        commands: Optional[Dict[str, Union['SubcommandGroup', Command]]] = None
    ) -> None:
        super().__init__()

        self.name = name
        self.description = description
        self.commands = commands or {}

    async def _inner_call(
        self,
        interaction: CommandInteraction,
        options: List[CommandInteractionOption]
    ) -> None:
        # This is O(n) but the list *should* only have one item unless
        # middleware modified it.
        found = [
            option for option in options
            if option.type is ApplicationCommandOption.subcommand
            or option.type is ApplicationCommandOption.subcommand_group
        ]
        if not found:
            raise ValueError(
                f'Subcommand group did not receive a subcommnad option - got: {options}'
            )

        subcommand = self.commands.get(found[0].value)
        if subcommand is None:
            raise LookupError(f'No subcommand found for interaction {interaction}')

        return await subcommand.invoke(interaction, found[0].options)

    def add_command(self, command: Union['SubcommandGroup', Command]) -> None:
        """Add a subcommand or sub-group.

        Parameters:
            command: The command or subcommand group to register.

        Raises:
            ValueError: If the command is already registered.
        """
        if command.name is None:
            raise ValueError('Cannot register unnamed command')

        if command.name in self.commands:
            raise ValueError(f"Command with name '{command.name}' already registered")

        self.commands[command.name] = command

    def remove_command(self, command: Union['SubcommandGroup', Command]) -> None:
        """Remove a subcommand or sub-group.

        Parameters:
            command:
                The command or subcommand group to remove. This can also be its
                name.

        Raises:
            ValueError: There is no command with that name.
            RuntimeError: The passed in command is not the registered one.
        """
        if command.name is None:
            raise ValueError('Cannot remove unnamed command')

        found = self.commands.get(command.name)
        if not found:
            raise ValueError(f"Cannot find registered command '{command.name}'")

        if found is not command:
            raise RuntimeError(
                f"Registered command '{command.name}' is not the command passed in"
            )

        del self.commands[command.name]

    def group(
        self,
        *,
        name: str,
        description: str,
    ) -> 'SubcommandGroup':
        """Create a nested subcommand group without a callback.

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

        Returns:
            The created and registered subcommand group.
        """
        group = SubcommandGroup(name=name, description=description)
        self.add_command(group)
        return group

    @overload
    def command(self, callback: Callback[P, RT]) -> Command[P, RT]:
        ...

    @overload
    def command(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Callable[[Callback[P, RT]], Command[P, RT]]:
        ...

    def command(
        self,
        callback: Optional[Callback[P, RT]] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Union[Command[P, RT], Callable[[Callback[P, RT]], Command[P, RT]]]:
        """Create and register a subcommand on this group.

        This decorator can be used both with and without parentheses.

        Parameters:
            callback: This gets filled by the decorator.
            name: The name of the subcommand.
            description: The description of the subcommand.

        Returns:
            The command, once decorated on the callback.
        """
        def decorator(func: Callback[P, RT]) -> Command[P, RT]:
            subcommand = Command(func, name=name, description=description)
            self.add_command(subcommand)
            return subcommand

        if callback is not None:
            return decorator(callback)

        return decorator


def _option_payload(option: OptionClass) -> ApplicationCommandOptionData:
    if option.name is None or option.type is None or option.description is None:
        raise ValueError('Missing required option values')

    data = {
        'name': option.name,
        'type': option.type.enum.value,
        'description': option.description,
        'required': True if option.required is None else option.required,
    }

    if option.choices is not None:
        # We store choices with the name as the key and value being the
        # value but Discord expects a payload with explicit name and value
        # keys so we need to convert it.
        choices = [{'name': k, 'value': v} for k, v in option.choices.items()]
        data['choices'] = choices

    if option.min is not None:
        data['min_value'] = option.min

    if option.max is not None:
        data['max_value'] = option.max

    # Static type checkers don't understand how the dictionary is built (but
    # even if it did, it's possible that the final dictionary does not follow
    # the type correctly).
    return data  # type: ignore


def _subcommand_payload(command: Command) -> ApplicationCommandOptionData:
    return {
        'type': ApplicationCommandOption.subcommand.value,
        'name': command.name,
        'description': command.description,
        'options': [
            _option_payload(option) for option in command.options.values()
        ]
    }  # type: ignore


def _group_payload(group: SubcommandGroup) -> ApplicationCommandOptionData:
    return {
        'type': ApplicationCommandOption.subcommand_group.value,
        'name': group.name,
        'description': group.description,
        'options': [
            _subcommand_payload(command) if isinstance(command, Command) else
            _group_payload(command)
            for command in group.commands.values()
        ]
    }  # type: ignore


def command_payload(command: Union[Command, SubcommandGroup]) -> ApplicationCommandPayload:
    """Generate the dictionary payload for the command.

    This can be used to turn commands into their payloads used to register them
    with Discord using the REST API.

    Parameters:
        command: The command to generate the payload for.

    Returns:
        Dictionary payload for the command.
    """
    if isinstance(command, Command):
        options = [_option_payload(option) for option in command.options.values()]
    else:
        options = [
            _subcommand_payload(command) if isinstance(command, Command) else
            _group_payload(command)
            for command in command.commands.values()
        ]

    return {
        'name': command.name,
        'type': 1,
        'description': command.description,
        'options': options
    }  # type: ignore
