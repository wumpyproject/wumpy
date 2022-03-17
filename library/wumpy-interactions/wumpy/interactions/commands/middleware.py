import time
from enum import Enum
from functools import partial, wraps
from typing import Callable, Dict, Hashable, TypeVar
from weakref import WeakValueDictionary

import anyio

from ..models import CommandInteraction
from .base import CommandCallback, MiddlewareCallback

__all__ = (
    'MiddlewareDecorator', 'CheckFailure', 'check', 'BucketType', 'max_concurrency',
)


CommandT = TypeVar('CommandT', bound=CommandCallback)
MiddlewareDecorator = Callable[[CommandT], CommandT]


class CheckFailure(Exception):
    """Raised when a check for an application command fails.

    Checks are encouraged to raise their own subclass of this exception, but it
    will automatically be raised if the check only returned a falsely value.
    """
    pass


class CheckMiddleware:
    call_next: MiddlewareCallback
    predicate: MiddlewareCallback

    __slots__ = ('call_next', 'predicate')

    def __init__(
        self,
        call_next: MiddlewareCallback,
        *,
        predicate: MiddlewareCallback
    ) -> None:
        self.call_next = call_next

        self.predicate = predicate

    async def __call__(self, interaction: CommandInteraction) -> None:
        if await self.predicate(interaction):
            await self.call_next(interaction)
        else:
            raise CheckFailure(f'Check {self.predicate} failed for interaction {interaction}')


def check(predicate: MiddlewareCallback) -> MiddlewareDecorator:
    """Create a check for an application command.

    This is a public wrapper over the middleware API to simplify creating
    checks.

    Examples:

        ```python
        from wumpy import interactions
        from wumpy.interactions import InteractionApp, MiddlewareDecorator, CommandInteraction


        # MiddlewareDecorator is a type alias to make the return type easier to
        # annotate and use.
        def on_version(v: int) -> MiddlewareDecorator:
            async def predicate(interaction: CommandInteraction) -> bool:
                return interaction.version == v
            return interactions.check(predicate)


        app = InteractionApp(...)


        @on_version(1)
        @app.command()
        async def ping(interaction: CommandInteraction) -> None:
            \"\"\"Pong!\"\"\"
            await interaction.respond('Pong!')
        ```

    Parameters:
        predicate: A callable that takes the interaction and returns a boolean.

    Returns:
        A decorator to apply to the application command.
    """
    @wraps(predicate)
    def wrapper(command: CommandT) -> CommandT:
        command.push_middleware(partial(CheckMiddleware, predicate=predicate))
        return command
    return wrapper


class BucketType(Enum):
    user = 0
    member = 1

    guild = 2
    channel = 3

    target = 7

    def __call__(self, inter: CommandInteraction) -> Hashable:
        cls = type(self)
        return {
            cls.user: inter.author.id,
            cls.member: (inter.author.id, inter.guild_id),

            cls.guild: inter.guild_id,
            cls.channel: inter.channel_id,
            cls.target: inter.target_id,
        }[self]


class MaxConcurrencyMiddleware:

    call_next: MiddlewareCallback

    number: int
    key: Callable[[CommandInteraction], Hashable]

    semaphores: 'WeakValueDictionary[Hashable, anyio.Semaphore]'

    __slots__ = ('call_next', 'number', 'key', 'semaphores')

    def __init__(
        self,
        call_next: MiddlewareCallback,
        *,
        number: int,
        key: Callable[[CommandInteraction], Hashable],
    ) -> None:
        self.call_next = call_next

        self.number = number
        self.key = key

        self.semaphores = WeakValueDictionary()

    async def __call__(self, interaction: CommandInteraction) -> None:
        key = self.key(interaction)

        semaphore = self.semaphores.setdefault(key, anyio.Semaphore(self.number))

        try:
            semaphore.acquire_nowait()
        except anyio.WouldBlock:
            await interaction.defer()
            await semaphore.acquire()

        try:
            await self.call_next(interaction)
        finally:
            semaphore.release()


def max_concurrency(
    number: int,
    key: Callable[[CommandInteraction], Hashable]
) -> MiddlewareDecorator:
    """Create a middleware that limits concurrent uses of a command.

    There are utility functions under `wumpy.interactions.BucketType` for the
    `key` parameter.

    Examples:

        ```python
        from wumpy import interactions
        from wumpy.interactions import InteractionApp, CommandInteraction


        app = InteractionApp(...)


        @interactions.max_concurrency(1, interactions.BucketType.guild)
        @app.command()
        async def ping(interaction: CommandInteraction) -> None:
            \"\"\"Pong!\"\"\"
            await interaction.respond('Pong!')
        ```

    Parameters:
        number: The number of concurrent uses of the command.
        key: A callable to determine the key to use for the bucket.

    Returns:
        A decorator to apply to the application command.
    """
    def decorator(command: CommandT) -> CommandT:
        command.push_middleware(partial(MaxConcurrencyMiddleware, key=key, number=number))
        return command
    return decorator
