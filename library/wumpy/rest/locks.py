from types import TracebackType
from typing import Optional, Type

import anyio

__all__ = ('RateLimit',)


class RateLimit:
    """Wrapper over a simple AnyIO lock that allows deferring the release."""

    deferred: bool

    __slots__ = ('deferred', '_lock')

    def __init__(self) -> None:
        self.deferred = False
        self._lock = anyio.Lock()

    async def __aenter__(self) -> 'RateLimit':
        await self._lock.acquire()
        self.deferred = False
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        if not self.deferred:
            self._lock.release()

    def defer(self) -> None:
        """Defer the lock from releasing during the next __aexit__.

        This is used to release the lock later on, while still exiting.
        """
        self.deferred = True

    def release(self) -> None:
        """Release the ratelimit lock."""
        self._lock.release()
