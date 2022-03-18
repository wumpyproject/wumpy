import inspect
from typing import Any, Dict, List, Optional, OrderedDict, TypeVar

from typing_extensions import ParamSpec
from wumpy.models import CommandInteraction

from .base import Callback, CommandCallback
from .option import OptionClass

__all__ = ('SlashCommand',)


P = ParamSpec('P')
RT = TypeVar('RT')


class SlashCommand(CommandCallback[P, RT]):
    """Top-level slashcommand callback.

    Currently subcommand groups and subcommands are not supported.
    """

    name: Optional[str]
    description: Optional[str]
    options: 'OrderedDict[str, OptionClass]'

    def __init__(
        self,
        callback: Optional[Callback[P, RT]] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        self.name = name
        self.description = description

        self.options = OrderedDict()

        # __init__() will dispatch the processing methods below which means
        # that we need to set the attributes above first.
        super().__init__(callback)

    async def _inner_call(self, interaction: CommandInteraction) -> RT:
        # We receive options as a JSON array but this is inefficient to lookup
        mapping = {option.name: option for option in interaction.options}
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
                # We don't need to check for non-defaulted keyword-only parameters following
                # defaulted keyword-only parameters because that would normally be allowed by
                # Python syntax.
                if option.has_default:
                    kw_defaults[option.param] = option.default

        self.callback.__defaults__ = tuple(defaults)
        self.callback.__kwdefaults__ = kw_defaults
