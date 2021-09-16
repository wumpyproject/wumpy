import inspect
from functools import partial
from typing import Callable, Coroutine, Dict, List, TypeVar, Union

import anyio.abc

from ...utils import MISSING
from ..base import CommandInteractionOption
from .option import ApplicationCommandOption, OptionClass

CT = TypeVar('CT')


class CommandCallback:
    """Base for simple wrapper over a callback with options.

    Application Commands use this in some form to eventually invoke a callback
    with the options and interaction passed.
    """

    options: Dict[str, OptionClass]

    _callback: Callable[..., Coroutine]

    __slots__ = ('_callback', 'options')

    def __init__(self, callback: Callable[..., Coroutine] = MISSING) -> None:
        self.options = {}

        self.callback = callback

    def _set_callback(self, function) -> None:
        # It is harder to override a property and call super()s setter, instead
        # we can use a method which is easier.
        signature = inspect.signature(function)

        for param in signature.parameters.values():
            if isinstance(param.default, OptionClass):
                option = param.default
            else:
                option = OptionClass()

            option.update(param)
            self.options[option.name] = option

        self._callback = function

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, function) -> None:
        return self._set_callback(function)

    def __call__(self, function: CT) -> CT:
        # By doing this we allow commands to be constructed without callbacks,
        # that way someone can assign a command to a variable if it doesn't
        # need a callback (which would litter the code).
        self.callback = function
        return function

    def option(
        self,
        param: str,
        *,
        name: str = MISSING,
        description: str = MISSING,
        required: bool = False,
        choices: Dict[str, Union[str, int, float]] = MISSING,
        type: ApplicationCommandOption = MISSING
    ) -> Callable[[CT], CT]:
        """Edit an option to the command through a decorator interface."""
        def void(func: CT) -> CT:
            return func

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

        return void

    def handle_interaction(
        self,
        interaction,
        options: List[CommandInteractionOption],
        *,
        tg: anyio.abc.TaskGroup
    ) -> None:
        """Invoke the callback with the interaction and options."""
        args, kwargs = [], {}

        for option in options:
            param = self.options[option.name]
            if param.kind in {param.kind.POSITIONAL_ONLY, param.kind.POSITIONAL_OR_KEYWORD}:
                args.append(param.resolve(interaction, option))
            else:
                kwargs[param.param] = param.resolve(interaction, option)

        tg.start_soon(partial(self.callback, interaction, *args, **kwargs))
