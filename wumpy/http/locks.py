import asyncio
from collections import deque
from typing import Any

import cython
from typing_extensions import Deque, Protocol

__all__ = ('Lock', 'RateLimit')


class Lock(Protocol):
    """A basic lock for respecting rate limits."""

    __slots__ = ()

    def __init__(self, event: asyncio.Event) -> None:
        """Initialize the lock with an asyncio.Event acting as a global lock."""
        ...

    async def __aenter__(self) -> 'Lock':  # Forward reference to the class itself
        ...

    async def __aexit__(self, *_: Any) -> None:
        ...

    async def acquire(self) -> None:
        """Acquire the lock.

        The implementation of this lock should wait if the lock is currently
        locked, waiting until it is released.
        """
        ...

    def defer(self) -> None:
        """Defer the lock from automatically releasing.

        This is used when there are no requests remaining in the current
        ratelimit, and the lock is getting a later scheduled call to
        `release()` so it should not be unlocked when exiting.
        """
        ...

    def release(self) -> None:
        """Release the lock.

        This function should explicitly release the lock.
        """
        ...


@cython.cclass
class RateLimit:
    """An API rate limit lock and default implementation of the Lock protocol."""

    deferred: cython.bint
    locked = cython.declare(cython.bint, visibility='readonly')

    event: asyncio.Event
    _waiters: Deque[asyncio.Future[None]]

    # __slots__ = ('deferred', 'locked', 'event', '_waiters')

    def __init__(self, event: asyncio.Event) -> None:
        self.deferred = False
        self.locked = False

        self.event = event
        self._waiters = deque()

    async def __aenter__(self) -> 'RateLimit':
        await self.acquire()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if not self.deferred:
            self.release()

    @cython.cfunc
    def _next(self) -> cython.void:
        """Wake up a waiting future."""
        while self._waiters:
            future = self._waiters.popleft()
            if not future.done():
                future.set_result(None)
                break

    def defer(self) -> None:
        """Defer the lock from releasing during the next __aexit__.

        This is used to release the lock later on, while still exiting.
        """
        self.deferred = True

    async def acquire(self) -> None:
        """Acquire a lock, this will wait until the lock is released."""
        if self.locked:
            future = asyncio.get_running_loop().create_future()
            self._waiters.append(future)
            try:
                await future  # Wait until manually resolved
            except asyncio.CancelledError as e:
                if not self.locked and not future.cancelled():
                    # The future was resolved, but before anything could
                    # happen the task awaiting this was cancelled (not the
                    # future itself). We need to start the next future in line.
                    self._next()
                raise e

        self.locked = True
        await self.event.wait()

    def release(self) -> None:
        """Release the rate limit lock and attempt to wake up a future."""
        self.locked = False
        self.deferred = False

        self._next()
