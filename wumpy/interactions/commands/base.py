from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

import anyio.abc

from ...utils import MISSING
from ..base import CommandInteraction

CT = TypeVar('CT')


class CommandCallback:
    """The base for application commands. A wrapped callback."""

    name: str
    parent: Any

    _callback: Optional[Callable[..., Coroutine]]

    __slots__ = ('name', '_callback')

    def __init__(
        self,
        callback: Optional[Callable[..., Coroutine]] = None,
        *,
        name: str = MISSING
    ) -> None:
        self.name = name

        self.callback = callback

    def _set_callback(self, function: Callable[..., Coroutine]) -> None:
        self.name = function.__name__ if self.name is MISSING else self.name

        self._callback = function

    @property
    def callback(self) -> Optional[Callable[..., Coroutine]]:
        return self._callback

    @callback.setter
    def callback(self, function: Optional[Callable[..., Coroutine]]) -> None:
        if function is None:
            self._callback = function
            return

        return self._set_callback(function)

    # ParamSpec would allow us to annotate these arguments but it is 3.10+
    def __call__(self, *args, **kwargs) -> Coroutine:
        assert self.callback is not None, 'Cannot call command without callback'

        return self.callback(*args, **kwargs)

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        *args,
        tg: anyio.abc.TaskGroup,
        **kwargs
    ) -> None:
        """Invoke the attached callbacks with the task group."""
        raise NotImplementedError()

