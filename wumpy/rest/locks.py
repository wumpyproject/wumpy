"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
from collections import deque
from typing import Any

from typing_extensions import Deque as DequeType
from typing_extensions import Protocol

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


class RateLimit:
    """An API rate limit lock and default implementation of the Lock protocol."""

    deferred: bool
    locked: bool

    event: asyncio.Event
    _waiters: DequeType[asyncio.Future]

    __slots__ = ('__weakref__', 'deferred', 'locked', 'event', '_waiters')

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

    def _next(self) -> None:
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
