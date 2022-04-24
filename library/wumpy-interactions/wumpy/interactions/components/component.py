import collections
from typing import (
    Any, Callable, Coroutine, Deque, Dict, Generic, List, Optional, Tuple,
    TypeVar, Union
)

import anyio

from ..models import ComponentInteraction

__all__ = ['Component']


T = TypeVar('T')
Coro = Coroutine[Any, Any, T]


class Result(Generic[T]):
    """Synchronizing Event but modified to pass a result."""

    value: T

    __slots__ = ('_event', 'value')

    def __init__(self) -> None:
        self._event = anyio.Event()

    def is_set(self) -> bool:
        return self._event.is_set()

    def set(self, value: T) -> None:
        self._event.set()
        self.value = value

    async def wait(self) -> T:
        await self._event.wait()
        if not hasattr(self, 'value'):
            raise RuntimeError('Result woken up without value')

        return self.value  # value should now be set


class Component:
    """Implementation for awaiting components until they are called.

    All components inherit from this base class.
    """

    _callback: Optional[Callable[[ComponentInteraction], Coro[object]]]

    _waiters: List[
        Tuple[
            Callable[[ComponentInteraction], bool],
            Result[ComponentInteraction]
        ]
    ]

    __slots__ = ('_callback', '_waiters')

    def __init__(
        self,
        callback: Optional[Callable[[ComponentInteraction], Coro[object]]] = None,
    ) -> None:
        self._callback = callback
        self._waiters = []

    async def __call__(
        self,
        check: Callable[[ComponentInteraction], bool] = lambda i: True,
        *,
        timeout: Optional[float] = None
    ) -> ComponentInteraction:
        event: Result[ComponentInteraction] = Result()
        self._waiters.append((check, event))

        with anyio.fail_after(timeout):
            return await event.wait()

    def set_callback(
        self,
        callback: Callable[[ComponentInteraction], Coro[object]],
        *,
        override: bool = False
    ) -> None:
        """Set the callback for this component.

        Parameters:
            callback: Asynchornous callback that takes an interaction.
            override: Whether to override the callback if it is already set.

        Raises:
            RuntimeError: There is already a callback but `override` is False.
        """
        if self._callback is not None and not override:
            raise RuntimeError("Callback is already set but 'override' is False")

        self._callback = callback

    async def invoke(self, interaction: ComponentInteraction) -> None:
        async with anyio.create_task_group() as tg:
            if self._callback is not None:
                tg.start_soon(self._callback, interaction)

            popped: Deque[int] = collections.deque()
            for index, (check, event) in enumerate(self._waiters):
                if check(interaction):
                    event.set(interaction)
                    popped.append(index)

            # Removing items from a list while iterating it, gives very odd
            # behaviour you have to account for. This is the easiest way
            for index in popped:
                del self._waiters[index]

    def to_dict(self) -> Union[List[Any], Dict[str, Any]]:
        """Method meant to be implemented by subclasses."""
        raise NotImplementedError()
