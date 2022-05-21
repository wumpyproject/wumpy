import logging
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

from .config import RatelimiterContext
from .errors import RateLimited, ServerException
from .route import Route

__all__ = ('Ratelimiter', 'DictRatelimiter')


_log = logging.getLogger(__name__)


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
        '_lock', '_ratelimited', '_event', '_limit', '_remaining', '_reset_at',
        '_in_progress', '__weakref__'
    )

    def __init__(self, limit: int = 1, remaining: int = 1) -> None:
        self._lock = anyio.Lock()

        self._ratelimited = anyio.Event()
        self._ratelimited.set()

        self._event = anyio.Event()

        self._limit = limit
        self._remaining = remaining
        self._reset_at = None

        self._in_progress = 0

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        self.release()

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
        self._event = anyio.Event()

    def acquire_nowait(self) -> None:
        """Acquire the semaphore, raising an error if blocking is necessary."""
        if self._lock.locked or not self._ratelimited.is_set():
            raise anyio.WouldBlock

        if self._remaining >= 1:
            self._remaining -= 1
            self._in_progress += 1
            return

        if self._reset_at is not None and self._reset_at < time.perf_counter():
            self._remaining = self._limit - 1
            self._reset_at = None
            self._in_progress += 1
            return

        raise anyio.WouldBlock

    async def acquire(self) -> None:
        """Decrement the semaphore value, blocking if necessary."""
        await anyio.lowlevel.checkpoint_if_cancelled()

        try:
            self.acquire_nowait()
        except anyio.WouldBlock:
            async with self._lock:
                await self._ratelimited.wait()

                # We have to repeat all code inside of acquire_nowait() because
                # while we were waiting on the lock and ratelimited event these
                # values may have changed...

                if self._remaining >= 1:
                    self._remaining -= 1
                    self._in_progress += 1
                    return

                if self._reset_at is None:
                    _log.debug('Waiting for reset_at timestamp to be updated for lock')

                    await self._event.wait()

                    # Another task may have updated the remaining tokens when
                    # it got ratelimit information (or released the lock).
                    if self._remaining >= 1:
                        self._remaining -= 1
                        self._in_progress += 1
                        return

                if self._reset_at is None:
                    raise RuntimeError(
                        'Ratelimit was notified of a new reset, but no reset time was set.'
                    )

                if self._reset_at < time.perf_counter():
                    self._remaining = self._limit - 1
                    self._reset_at = None
                    self._in_progress += 1
                    return

                else:
                    await anyio.sleep(self._reset_at - time.perf_counter())
                    self._remaining = self._limit - 1
                    self._reset_at = None
                    self._in_progress += 1
        else:
            await anyio.lowlevel.cancel_shielded_checkpoint()

    def release(self) -> None:
        self._in_progress -= 1

        # If all requests fail (especially if this is the first request on this
        # newly created lock) then we may cause a dead-lock because there are
        # no remaining tokens and we don't know when the next reset will be.
        if self._in_progress > 0 or self._remaining > 0:
            return

        # Since there are no more requests which can give us ratelimit
        # information, we should artificially add another token to ensure that
        # at least one request can go through and give us ratelimit information
        # again so that we can lock efficiently.
        if self._reset_at is not None:
            self._remaining = 1

            # In-case there are requests waiting for a reset_at, we should wake
            # them up because they are occupying the lock.
            self._event.set()
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
    async def acquire(self) -> AsyncGenerator[
        Callable[[Mapping[str, str]], Awaitable[object]], None
    ]:
        await self._parent.wait()

        if RatelimiterContext.abort_if_ratelimited():
            try:
                self._lock.acquire_nowait()
            except anyio.WouldBlock:
                raise RateLimited(429, {})
        else:
            await self._lock.acquire()

        try:
            yield self.update
        except ServerException as exc:
            if exc.status_code == 503:
                raise

            _log.warning(
                f'Unconditionally backing off after receiving {exc.status_code}-response'
            )
            # For status code 500, 502 and 504 its best to exponentially sleep
            await anyio.sleep(1 + exc.attempt * 2)

        except RateLimited as exc:
            if RatelimiterContext.abort_if_ratelimited():
                raise

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
                _log.warning(
                    f'Request to {self._route} hit the global ratelimit;'
                    f' retrying in {retry} seconds.'
                )
                self._parent.lock()
            else:
                _log.warning(
                    f'Request to {self._route} was ratelimited; retrying in {retry} seconds.'
                )

            self._lock.lock()
            try:
                await anyio.sleep(float(retry))
            finally:
                self._lock.unlock()

                if globally:
                    self._parent.unlock()

            _log.debug(f'Finished sleeping from ratelimit for {self._route}')
        finally:
            self._lock.release()

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
            self._lock.reset_at = datetime.fromtimestamp(float(reset), timezone.utc)


class GlobalRatelimit:
    """Ratelimit lock for respecting the global ratelimit."""

    _event: anyio.Event
    _lock: anyio.Lock

    _reset: Optional[float]
    _value: int

    __slots__ = ('_event', '_lock', '_reset', '_rate', '_value')

    def __init__(self, rate: int) -> None:
        self._event = anyio.Event()
        self._event.set()

        self._lock = anyio.Lock()

        self._reset = None
        self._rate = rate
        self._value = rate

    async def wait(self) -> None:
        async with self._lock:
            await self._event.wait()

            if self._reset is None or self._reset < time.perf_counter():
                self._reset = time.perf_counter() + 1
                self._value = self._rate - 1

            elif self._value <= 0:
                _log.debug('Avoiding global ratelimit by sleeping until reset.')

                await anyio.sleep(self._reset - time.perf_counter())
                self._reset = time.perf_counter() + 1
                self._value = self._rate - 1
            else:
                self._value -= 1

    def lock(self) -> None:
        # If the event isn't set, then another task has already locked the
        # ratelimiter and there may be waiters which we should make sure to not
        # loose forever.
        if self._event.is_set():
            self._event = anyio.Event()
        else:
            _log.debug('Not globally locking ratelimiter as it is already locked')

    def unlock(self) -> None:
        self._event.set()


class DictRatelimiter:
    """The simplest and default implementation of the RateLimiter protocol.

    This implementation stores all its locks as capacity limiters in
    (weakref)dictionaries in-memory, this means that they can't be shared
    across processes (such as to another shard).

    There is one parameter that can be passed on instantiation, which is the
    amount of requests that can be made each second according to the global
    ratelimit.

    Attributes:
        buckets: A dictionary of endpoints to their ratelimit buckets.
        limiters:
            A weak dictionary of buckets + their major parameters to the
            underlying ratelimit locks.
        fallbacks:
            Fallback ratelimit locks to use before appropriate buckets are
            known.
    """

    _global_rl: GlobalRatelimit

    buckets: Dict[str, str]
    locks: 'WeakValueDictionary[str, Ratelimit]'
    fallbacks: 'WeakValueDictionary[str, Ratelimit]'

    __slots__ = ('_tasks', '_global_rl', 'buckets', 'locks', 'fallbacks')

    def __init__(self, global_rate: int = 50) -> None:
        self._global_rl = GlobalRatelimit(global_rate)

        self.buckets = {}  # Route endpoint to X-RateLimit-Bucket

        # By using a WeakValueDictionary, Python can deallocate locks if
        # they're not in any way used (waiting, or acquired). This way we
        # don't have to deal with any form of LRU structure.
        # This is important as each bucket + major parameters gets a lock in
        # this dictionary, even if you only send one request.
        self.locks = WeakValueDictionary()

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
        """Get a ratelimit lock by its endpoint.

        Parameters:
            route: The route that a request is about to be made to.

        Returns:
            A proxy ratelimit lock that continues the ratelimiter protocol.
        """
        bucket = self.buckets.get(route.endpoint)
        if not bucket:
            _log.debug(
                f'Using fallback ratelimit lock {route.endpoint + route.major_params}'
            )
            # Fallback until we get X-RateLimit-Bucket information with the
            # 'bucket' parameter called in set_lock()
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
        """Update and set a lock for a route.

        Parameters:
            route: The route that the request was made to.
            bucket: The received X-RateLimit-Bucket header value.
            lock: The current ratelimit lock.

        Returns:
            The lock for the bucket. This is either another lock if the bucket
            already had a lock, or the one passed into the method.
        """
        self.fallbacks.pop(route.endpoint + route.major_params, None)

        self.buckets[route.endpoint] = bucket
        return self.locks.setdefault(bucket + route.major_params, lock)

    def lock(self) -> None:
        """Globally lock all locks across the ratelimiter."""
        self._global_rl.lock()

    def unlock(self) -> None:
        """Unlock all locks across the ratelimiter."""
        self._global_rl.unlock()

    async def wait(self) -> None:
        """Wait for the global ratelimit to send a request."""
        await self._global_rl.wait()
