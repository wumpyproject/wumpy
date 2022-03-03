import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import TracebackType
from typing import (
    AsyncContextManager, AsyncGenerator, Awaitable, Callable, Dict, Mapping,
    Optional, Type
)
from weakref import WeakValueDictionary

import anyio
import anyio.lowlevel
from typing_extensions import Self

from .errors import RateLimited, ServerException
from .route import Route

__all__ = ('Ratelimiter', 'DictRatelimiter')


# The type allows the usage to the right of the code.
Ratelimiter = AsyncContextManager[  # async with ratelimiter as rl:
    Callable[[Route], AsyncContextManager[  # async with rl(route) as lock:
        Callable[[Mapping[str, str]], Awaitable[object]]  # await lock(headers)
    ]]
]


class Ratelimit:
    """A special type of timed semaphore.

    This is very similar to AnyIO's `Semaphore` or `CapacityLimiter`
    implementation, but adapted to work for Discord ratelimits.

    A `Ratelimit` is made up of one lock and two events, along with the
    information from the ratelimit headers. The purpose of the lock is to be
    able to queue tasks trying to acquire the ratelimit, because if one task
    needs to sleep until the next reset then all the following tasks needs to
    do so as well.

    The two events are used a bit differently, the first is used to completely
    lock the ratelimit in the case that a 429 response is received. The second
    event allows the ratelimit to notify itself once another reset is known,
    because Discord does not provide a "per" header so it cannot be calculated
    in advance.
    """

    # Previously this class had a move() feature to handle two buckets merging
    # while having multiple waiters. It introduced a lot of code complexity and
    # was only there for an extremely rare condition that required:
    # - Discord to merge two buckets
    # - There to be multiple tasks waiting on the same route and major params
    #
    # When this is not handled, the worst that can happen is an 429 response
    # from Discord, which in of itself will be handled correctly. This is not
    # the end of the day really.

    _lock: anyio.Lock
    _ratelimited: anyio.Event
    _event: anyio.Event

    _limit: int
    _remaining: int
    _reset_at: Optional[float]

    __slots__ = (
        '_lock', '_ratelimited', '_event', '_limit', '_remaining', '_reset_at', '__weakref__'
    )

    def __init__(self, limit: int = 1, remaining: int = 1) -> None:
        self._lock = anyio.Lock()

        self._ratelimited = anyio.Event()
        self._ratelimited.set()

        self._event = anyio.Event()
        self._event.set()

        self._limit = limit
        self._remaining = remaining
        self._reset_at = None

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        pass

    @property
    def remaining(self) -> int:
        """The remaining number of tokens."""
        return self._remaining

    @remaining.setter
    def remaining(self, value: int) -> None:
        # We only want to update the remaining tokens if they are less than
        # what we track locally, since a request can be in-progress but not yet
        # received by Discord (making the local count lower).
        self._remaining = min(self._remaining, value)

    @property
    def limit(self) -> int:
        """The maximum number of tokens that can be acquired in the window."""
        return self._limit

    @limit.setter
    def limit(self, value: int) -> None:
        diff = self._limit - self._remaining

        self._limit = value
        self._remaining = self._limit - diff

    @property
    def reset_at(self) -> Optional[float]:
        """The `time.perf_counter()` time at which a new window starts."""
        return self._reset_at

    @reset_at.setter
    def reset_at(self, value: datetime) -> None:
        delta = value - datetime.now(timezone.utc)
        self._reset_at = time.perf_counter() + delta.total_seconds()
        self._event.set()

    async def acquire(self) -> None:
        """Decrement the semaphore value, blocking if necessary."""
        async with self._lock:
            await self._ratelimited.wait()

            if self._remaining >= 1:
                self._remaining -= 1
                return

            if self._reset_at is None:
                await self._event.wait()

            if self._reset_at is None:
                raise RuntimeError(
                    'Ratelimit was notified of a new reset, but no reset time was set.'
                )

            if self._reset_at < time.perf_counter():
                self._remaining = self._limit - 1
                self._reset_at = None
                self._event = anyio.Event()
                return

            else:
                await anyio.sleep(self._reset_at - time.perf_counter())
                self._remaining = self._limit - 1
                self._reset_at = None
                self._event = anyio.Event()

    def lock(self) -> None:
        self._ratelimited = anyio.Event()

    def unlock(self) -> None:
        self._ratelimited.set()


class _RouteRatelimit:
    """Proxy implementing the rest of the ratelimiter protocol."""

    __slots__ = ('_lock', '_parent', '_route', 'deferred')

    def __init__(self, parent: 'DictRatelimiter', lock: Ratelimit, route: Route) -> None:
        self._parent = parent
        self._lock = lock
        self._route = route

        self.deferred = False

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Callable[[Mapping[str, str]], Awaitable[object]], None]:
        await self._parent.global_event.wait()

        try:
            async with self._lock:
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

            self._lock.lock()
            await anyio.sleep(float(retry))
            self._lock.unlock()

            if globally:
                self._parent.unlock()

    async def update(self, headers: Mapping[str, str]) -> None:
        """Update the ratelimiter with the rate limit headers from Discord."""
        try:
            bucket = headers['X-RateLimit-Bucket']
        except KeyError:
            bucket = None
        else:
            # Update the ratelimiter with the bucket and remove the fallback
            # if present currently.
            self._lock = self._parent.set_lock(self._route, bucket, self._lock)

        try:
            limit = headers['X-RateLimit-Limit']
        except KeyError:
            pass
        else:
            self._lock.limit = int(limit)

        try:
            remaining = headers['X-RateLimit-Remaining']
        except KeyError:
            pass
        else:
            self._lock.remaining = int(remaining)

        try:
            reset = headers['X-RateLimit-Reset']
        except KeyError:
            return
        else:
            dt = datetime.fromtimestamp(float(reset), timezone.utc)
            self._lock.reset_at = dt


class DictRatelimiter:
    """The simplest and default implementation of the RateLimiter protocol.

    This implementation stores all its locks as capacity limiters in
    (weakref)dictionaries in-memory, this means that they can't be shared
    across processes (such as to another shard).

    Attributes:
        global_event:
            An anyio Event that gets set when the global ratelimit is hit which
            pauses all other requests.
        buckets: A dictionary of endpoints to their ratelimit buckets.
        limiters:
            A weak dictionary of buckets + their major parameters to the
            underlying capacity limiter.
        fallbacks:
            Fallback capacity limiters to use before appropriate buckets are
            known.
    """

    global_event: anyio.Event

    buckets: Dict[str, str]
    limiters: 'WeakValueDictionary[str, Ratelimit]'
    fallbacks: 'WeakValueDictionary[str, Ratelimit]'

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
        self.locks: 'WeakValueDictionary[str, Ratelimit]' = WeakValueDictionary()

        # Fallback locks before buckets get populated
        self.fallbacks = WeakValueDictionary()

    async def __aenter__(self) -> Callable[
        [Route], AsyncContextManager[
            Callable[[Mapping[str, str]], Awaitable[object]]
        ]
    ]:
        self._tasks = await anyio.create_task_group().__aenter__()
        return self.get_lock

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> Optional[bool]:
        # Our tasks simply consist of sleeping callbacks, there's no benefit to
        # waiting for them to finish when cleaning up.
        self._tasks.cancel_scope.cancel()
        return await self._tasks.__aexit__(exc_type, exc_val, traceback)

    def get_lock(
        self,
        route: Route
    ) -> AsyncContextManager[Callable[[Mapping[str, str]], Awaitable[object]]]:
        """Get a ratelimit lock by its endpoint."""
        bucket = self.buckets.get(route.endpoint)
        if not bucket:
            # Fallback until we get X-RateLimit-Bucket information in called
            # with set_lock().
            lock = self.fallbacks.setdefault(
                route.endpoint + route.major_params, Ratelimit()
            )
            return _RouteRatelimit(self, lock, route).acquire()

        # We have more accurate bucket information we can use together with the
        # major parameters..
        lock = self.locks.setdefault(bucket + route.major_params, Ratelimit())
        return _RouteRatelimit(self, lock, route).acquire()

    def set_lock(
        self,
        route: Route,
        bucket: str,
        lock: Ratelimit
    ) -> Ratelimit:
        """Update and set a lock for a route."""

        self.fallbacks.pop(route.endpoint + route.major_params, None)

        self.buckets[route.endpoint] = bucket
        return self.locks.setdefault(bucket + route.major_params, lock)

    def lock(self) -> None:
        """Globally lock all locks across the ratelimiter."""
        # If the global event isn't set, then another task has already locked
        # the ratelimiter.
        if self.global_event.is_set():
            self.global_event = anyio.Event()

    def unlock(self) -> None:
        """Unlock all locks across the ratelimiter."""
        self.global_event.set()  # Release the previous
