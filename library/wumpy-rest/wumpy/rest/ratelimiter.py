from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import TracebackType
from typing import (
    AsyncContextManager, AsyncGenerator, Awaitable, Callable, Coroutine, Dict,
    Mapping, Optional, Type, Union
)
from weakref import WeakValueDictionary

import anyio

from .errors import RateLimited, ServerException
from .route import Route

__all__ = ('RateLimiter', 'DictRateLimiter')


# The type allows the usage to the right of the code.
RateLimiter = AsyncContextManager[  # async with ratelimiter as rl:
    Callable[[Route], AsyncContextManager[  # async with rl(route) as lock:
        Callable[[Mapping[str, str]], Awaitable]  # await lock(headers)
    ]]
]
"""Complete typing information of a rate limiter as a type alias.

Don't be discourage by the somewhat complicated signature. The ratelimiter
itself is somewhat easy:

It starts off with an asynchronous context manager that allows you to setup
connections if you wish to. Inside this asynchronous context manager return a
callable (like a method on the instance) that when called with a route that the
requester will make a request towards returns another asynchronous context
manager.

This asynchronous context manager is now entered, and this is where you want to
acquire the underlying lock however it is now implemented. This then returns
another callable (but this time it will be `await`ed) that will take a mapping
representing the request headers and allow you to update the ratelimiter with
the rate limit headers from Discord.

Lastly all context managers are exited with potential exception information
depending on the status code which you should supress by returning a truthy
value if you wish the requester retry the request.
"""


def releaser(delay: Union[int, float], callback: Callable) -> Callable[[], Coroutine]:
    """Coroutine function factory for sleeping and then call the callback."""
    async def inner():
        try:
            await anyio.sleep(delay)
        finally:
            # The sleep could be cancelled and raise an exception, no matter
            # what we should call the callback and cleanup as to not leave
            # things in an invalid state.
            callback()
    return inner


class _RouteRateLimit:
    """Implementation of the RateLimit for the dictionary ratelimiter."""

    __slots__ = ('_lock', '_parent', '_route', 'deferred')

    def __init__(self, parent: 'DictRateLimiter', lock: anyio.Lock, route: Route) -> None:
        self._parent = parent
        self._lock = lock
        self._route = route

        self.deferred = False

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Callable[[Mapping[str, str]], Coroutine], None]:
        await self._parent.global_event.wait()

        try:
            await self._lock.acquire()
            yield self.update
        except ServerException as exc:
            if exc.status_code == 503:
                raise

            # For status code 500, 502 and 504 its best to exponentially sleep
            await anyio.sleep(1 + exc.attempt * 2)

        except RateLimited as exc:
            # The data is somewhat duplicated, which means we can try our best
            # to find it in different places.
            if isinstance(exc.data, dict):
                retry = exc.data.get('retry_after', 1 + exc.attempt * 2)
                globally = exc.data.get('global', False)
            else:
                try:
                    retry = exc.headers['X-RateLimit-Reset-After']
                except KeyError:
                    retry = 1 + exc.attempt * 2

                try:
                    globally = exc.headers['X-RateLimit-Scope'] == 'global'
                except KeyError:
                    globally = False

            # If this is a global ratelimit we should lock all requests from
            # attempting to access any endpoint.
            if globally:
                self._parent.lock()

            await anyio.sleep(float(retry))

            if globally:
                self._parent.unlock()

        finally:
            if not self.deferred:
                self._lock.release()

    async def update(self, headers: Mapping[str, str]) -> None:
        try:
            bucket = headers['X-RateLimit-Bucket']
        except KeyError:
            bucket = None

        # Update the fallback if this route is this using.
        self._parent[self._route] = bucket

        try:
            remaining = headers['X-RateLimit-Remaining']
        except KeyError:
            return

        # Release later when the ratelimit resets, this allows us to exit
        # without releasing the lock.
        self.deferred = True
        reset = datetime.fromtimestamp(float(remaining), timezone.utc)
        self._parent._tasks.start_soon(releaser(
            (reset - datetime.now(timezone.utc)).total_seconds(),
            self._lock.release
        ))


class DictRateLimiter:
    """The simplest and default implementation of the RateLimiter protocol.

    This implementation stores all locks and buckets in (weakref)dictionaries
    in-memory. Locks are not shared across processes.
    """

    global_event: anyio.Event

    buckets: Dict[Route, str]
    locks: WeakValueDictionary
    fallbacks: Dict[Route, anyio.Lock]

    __slots__ = ('_tasks', 'global_event', 'buckets', 'locks', 'fallbacks')

    def __init__(self) -> None:
        self.global_event = anyio.Event()
        self.global_event.set()

        self.buckets = {}  # Route endpoint to X-RateLimit-Bucket

        # By using a WeakValueDictionary, Python can deallocate locks if
        # they're not in any way used (waiting, or acquired). This way we
        # don't have to deal with any form of LRU structure.
        # This is important as each bucket + major parameters gets a lock in
        # this dictionary, even if you only send one request.
        self.locks = WeakValueDictionary()

        # Fallback locks before buckets get populated
        self.fallbacks = {}

    async def __aenter__(self) -> Callable[
        [Route], AsyncContextManager[
            Callable[[Mapping[str, str]], Awaitable]
        ]
    ]:
        self._tasks = await anyio.create_task_group().__aenter__()
        return self.__getitem__

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> Optional[bool]:
        return await self._tasks.__aexit__(exc_type, exc_val, traceback)

    def __getitem__(
        self,
        route: Route
    ) -> AsyncContextManager[Callable[[Mapping[str, str]], Awaitable]]:
        """Get a ratelimit lock by its endpoint."""
        if not isinstance(route, Route):
            raise KeyError

        bucket = self.buckets.get(route)
        if not bucket:
            # Fallback until we get X-RateLimit-Bucket information in update()
            lock = self.fallbacks.setdefault(route, anyio.Lock())
            return _RouteRateLimit(self, lock, route).acquire()

        lock = self.locks.setdefault(bucket + route.major_params, anyio.Lock())
        return _RouteRateLimit(self, lock, route).acquire()

    def __setitem__(self, route: Route, bucket: Optional[str]) -> None:
        if not isinstance(route, Route):
            raise KeyError

        if bucket and self.fallbacks.pop(route, None):
            self.buckets[route] = bucket

    def lock(self) -> None:
        """Globally lock all locks across the ratelimiter."""
        self.global_event = anyio.Event()

    def unlock(self) -> None:
        """Unlock all locks across the ratelimiter."""
        self.global_event.set()  # Release the previous
        self.global_event = anyio.Event()
