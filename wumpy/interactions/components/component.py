import re
from typing import (
    TYPE_CHECKING, Any, Callable, Coroutine, Dict, Generic, List, Optional,
    Tuple, TypeVar, Union
)

import anyio
from anyio.abc import TaskGroup

from ...models import DISCORD_EPOCH

if TYPE_CHECKING:
    from ..base import ComponentInteraction

__all__ = ('Component', 'ComponentEmoji')


RT = TypeVar('RT')


class Result(Generic[RT]):
    """Synchronizing Event but modified to pass a result."""

    __slots__ = ('event', 'value')

    def __init__(self) -> None:
        self.event = anyio.Event()

    def is_set(self) -> bool:
        return self.event.is_set()

    def set(self, value: RT) -> None:
        self.event.set()
        self.value = value

    async def wait(self) -> RT:
        await self.event.wait()
        return self.value  # value should now be set


class Component:
    """Base component that allows waiting until an interaction has been received for it."""

    callback: Optional[Callable[['ComponentInteraction'], Coroutine]]

    waiters: List[
        Tuple[
            Callable[['ComponentInteraction'], bool],
            Result['ComponentInteraction']
        ]
    ]

    __slots__ = ('callback', 'waiters')

    def __init__(
        self,
        callback: Optional[Callable[['ComponentInteraction'], Coroutine]] = None,
    ) -> None:
        self.callback = callback
        self.waiters = []

    async def __call__(
        self,
        check: Callable[['ComponentInteraction'], bool] = lambda i: True,
        *,
        timeout: Optional[float] = None
    ) -> 'ComponentInteraction':
        event: Result['ComponentInteraction'] = Result()
        self.waiters.append((check, event))

        with anyio.fail_after(timeout):
            return await event.wait()

    def handle_interaction(self, interaction: 'ComponentInteraction', *, tg: TaskGroup) -> None:
        if self.callback is not None:
            tg.start_soon(self.callback, interaction)

        for index, (check, result) in enumerate(self.waiters):
            if check(interaction):
                result.set(interaction)
                self.waiters.pop(index)

    def to_dict(self) -> Union[List[Any], Dict[str, Any]]:
        raise NotImplementedError()


class ComponentEmoji:
    """Emoji sent with components to Discord."""

    REGEX = re.compile(r'<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')

    __slots__ = ('animated', 'name', 'id')

    def __init__(
        self,
        *,
        name: str,
        animated: bool = False,
        # In the case of unicode Discord emojis these were created when Discord
        # was created.
        id: int = DISCORD_EPOCH << 22
    ) -> None:
        self.animated = animated
        self.name = name
        self.id = id

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, int):
            return self.id == other
        elif isinstance(other, str):
            return self.name == other
        elif isinstance(other, self.__class__):
            return self.id == other.id and \
                self.name == other.name and \
                self.animated == other.animated
        else:
            return NotImplemented

    @classmethod
    def from_string(cls, value: str) -> 'ComponentEmoji':
        match = cls.REGEX.match(value)
        if match:
            return cls(
                name=match.group('name'),
                animated=bool(match.group('animated')),
                id=int(match.group('id'))
            )

        # The regex didn't match, we'll just have to assume the user passed unicode
        return cls(name=value)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'name': self.name,
            'id': self.id,
            'animated': self.animated
        }
        # We should clean it for None values
        return {k: v for k, v in data.items() if v is not None}
