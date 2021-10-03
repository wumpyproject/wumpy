import sys
import traceback
from typing import Any, Callable, Coroutine, Dict, Generic, Optional, TypeVar

import anyio.abc
from typing_extensions import ParamSpec

from ...utils import MISSING
from ..base import CommandInteraction

__all__ = ('Callback', 'CommandCallback')


P = ParamSpec('P')
RT = TypeVar('RT')


Callback = Callable[P, Coroutine[Any, Any, RT]]


class CommandCallback(Generic[P, RT]):
    """The base for application commands. A wrapped callback.

    Attributes:
        name: The name of the command.
    """

    name: str

    _callback: Optional[Callback[P, RT]]

    __slots__ = ('name', '_callback')

    def __init__(
        self,
        callback: Optional[Callback[P, RT]] = None,
        *,
        name: str = MISSING
    ) -> None:
        self.name = name

        self.callback = callback

    def _set_callback(self, function: Callback[P, RT]) -> None:
        self.name = function.__name__ if self.name is MISSING else self.name

        self._callback = function

    @property
    def callback(self) -> Optional[Callback[P, RT]]:
        return self._callback

    @callback.setter
    def callback(self, function: Optional[Callback[P, RT]]) -> None:
        if function is None:
            self._callback = function
            return

        return self._set_callback(function)

    async def _call_wrapped(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Call the wrapped callback and propogate error handlers."""
        if self.callback is None:
            raise AttributeError("'callback' is not set to a function")

        try:
            await self.callback(*args, **kwargs)
        except Exception as exc:
            print("Ignoring exception in command handler '{self.name}'", file=sys.stderr)
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Coroutine[Any, Any, RT]:
        if self.callback is None:
            raise AttributeError("'callback' is not set to a function")

        return self.callback(*args, **kwargs)

    def handle_interaction(
        self,
        interaction: CommandInteraction,
        *args,
        tg: anyio.abc.TaskGroup,
        **kwargs
    ) -> None:
        """Invoke the attached callback with the task group.

        This is meant to be overriden by subclasses.

        Parameters:
            interaction: The interaction to pass onto the callback.
            args: Any additional arguments that subclasses require.
            tg: The task group to start the callback with.
            kwargs: Any additional keyword arguments that subclasses require.

        Exceptions:
            NotImplementedError: This method has not been overriden.
        """
        raise NotImplementedError()

    def to_dict(self) -> Dict[str, Any]:
        """Convert this callback into a payload to send to Discord."""
        return {'name': self.name}
