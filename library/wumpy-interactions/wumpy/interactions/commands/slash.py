import inspect
from typing import Any, Dict, List, Optional, OrderedDict, TypeVar

from typing_extensions import ParamSpec
from wumpy.models import CommandInteractionOption
from wumpy.models.interactions import ApplicationCommandOption

from ..models import CommandInteraction
from .base import Callback, CommandCallback
from .middleware import CommandMiddlewareMixin
from .option import OptionClass

__all__ = ('Subcommand', 'SubcommandGroup')


P = ParamSpec('P')
RT = TypeVar('RT')


class Subcommand(CommandMiddlewareMixin, CommandCallback[P, RT]):
    """Subcommand with a callback for its handling.

    Subcommands themselves cannot have other subcommands nested under them.
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

        return super()._process_callback(callback)

    def _process_param(self, index: int, param: inspect.Parameter) -> None:
        if index == 0 and param.annotation is not param.empty:
            # If this is the first parameter, we need to make sure it is
            # either not annotated at all or its set as the command interaction
            ann = param.annotation
            if isinstance(ann, type) and not issubclass(ann, CommandInteraction):
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


class SubcommandGroup(CommandMiddlewareMixin):
    """Group of subcommands forwarding interactions.

    Subcommand groups has other subcommand groups under them but they cannot be
    called on its own.
    """

    def __init__(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        commands: Dict[str, Subcommand]
    ) -> None:
        super().__init__()

        self.name = name
        self.description = description
        self.commands = commands

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
        ]
        if not found:
            raise ValueError(
                f'Subcommand group did not receive a subcommnad option - got: {options}'
            )

        subcommand = self.commands.get(found[0].value)
        if subcommand is None:
            raise LookupError(f'No subcommand found for interaction {interaction}')

        return await subcommand.invoke(interaction, found[0].options)
