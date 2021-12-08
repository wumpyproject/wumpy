import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, MutableMapping, Optional, Union
from urllib.parse import quote as urlquote
from weakref import WeakValueDictionary

from typing_extensions import Protocol

from ..models.base import Snowflake
from .locks import RateLimit
from .route import Route

__all__ = ('RateLimiter', 'DictRateLimiter')


    """


class RateLimiter(Protocol):
    """Lockkeeper taking care of respecting rate limits."""

    def __init__(self) -> None: ...

    async def get(self, route: Route) -> RateLimit:
        """Get a lock by the route about to be made a request towards.

        The implementation of this function should handle several endpoints
        having the same X-RateLimit-Bucket, after the request is made the
        `update()` method will be called with the X-RateLimit-Bucket header so
        that the ratelimiter has a chance to fill this cache.

        The reason this method is asynchronous is that it should also handle
        the global rate limit.
        """
        ...

    def update(self, route: Route, bucket: Optional[str]) -> None:
        """Update the ratelimiter with the X-RateLimit-Bucket header received.

        This function is called after the request, so that the ratelimiter
        has a chance to build its cache.
        """
        ...

    def lock(self) -> None:
        """Globally lock all locks across the ratelimiter.

        This is called when the requester experiences a 429 response, the
        ratelimiter is expected to somehow lock all locks it hands out.
        """
        ...

    def unlock(self) -> None:
        """Unlock all locks across the ratelimiter.

        This is called after the requester has waited through the ratelimit,
        and should do the opposite of `lock()`.
        """
        ...


class DictRateLimiter:
    """The simplest and default implementation of the RateLimiter protocol."""

    global_event: asyncio.Event

    buckets: Dict[str, str]
    locks: WeakValueDictionary
    fallbacks: Dict[str, RateLimit]

    __slots__ = ('global_event', 'buckets', 'locks', 'fallbacks')

    def __init__(self) -> None:
        # Global ratelimit lock
        self.global_event = asyncio.Event()
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

    def default(self, mapping: MutableMapping[str, RateLimit], key: str) -> RateLimit:
        """Get `key` from the mapping, if it isn't found initialize a RateLimit in its place."""
        lock = mapping.get(key)
        if not lock:
            lock = RateLimit()
            mapping[key] = lock

        return lock

    async def get(self, route: Route) -> RateLimit:
        """Get a lock by the route about to be made a request towards."""
        await self.global_event.wait()

        bucket = self.buckets.get(route.endpoint)
        if not bucket:
            # Fallback until we get X-RateLimit-Bucket information in update()
            return self.default(self.fallbacks, route.endpoint)

        return self.default(self.locks, bucket + route.major_params)

    def update(self, route: Route, bucket: Optional[str]) -> None:
        """Update the ratelimiter with the X-RateLimit-Bucket header received."""
        # Remove the fallback and update the buckets dict
        if bucket and self.fallbacks.pop(route.endpoint, None):
            self.buckets[route.endpoint] = bucket

    def lock(self) -> None:
        """Globally lock all locks across the ratelimiter."""
        self.global_event.clear()

    def unlock(self) -> None:
        """Unlock all locks across the ratelimiter."""
        self.global_event.set()
