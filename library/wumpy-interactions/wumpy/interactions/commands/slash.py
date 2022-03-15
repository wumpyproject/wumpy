import inspect
from typing import Optional, OrderedDict, TypeVar

from typing_extensions import ParamSpec
from wumpy.interactions.commands.base import CommandCallback

from .base import Callback

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
