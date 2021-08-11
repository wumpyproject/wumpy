import asyncio
from collections.abc import MutableMapping
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union
from urllib.parse import quote as urlquote
from weakref import WeakValueDictionary

from typing_extensions import Protocol

from ..models.base import Snowflake
from .locks import Lock, RateLimit

__all__ = ('Route', 'RateLimiter', 'DictRateLimiter')


class Route:
    """A route that a request should be made to.

    Containing information such as the endpoint, and parameters to use. Mainly
    used to figure out ratelimit handling. If the request made should have a
    request body this should be passed to the requester.
    """

    method: str
    path: str
    params: Dict[str, Union[str, int]]

    __slots__ = ('method', 'path', 'params')

    BASE = 'https://discord.com/api/v9'

    def __init__(self, method: str, path: str, **params: Union[str, int]) -> None:
        self.method = method
        self.path = path

        self.params = params

    def __repr__(self) -> str:
        return f'<Route {self.endpoint}>'

    @property
    def url(self) -> str:
        """Return a complete, formatted url that a request should be made to."""
        return self.BASE + self.path.format_map(
            # Replace special characters with the %xx escapes
            {k: urlquote(v) if isinstance(v, str) else v for k, v in self.params.items()}
        )

    @property
    def endpoint(self) -> str:
        """Return the Discord endpoint this route will request."""
        return f'{self.method} {self.path}'

    @property
    def major_params(self) -> str:
        """Return a string of the formatted major parameters."""
        params = ':{0}/{1}/{2}'.format(
            self.params.get('guild_id', 0), self.params.get('channel_id', 0),
            self.params.get('webhook_id', 0)
        )

        # Discord handles messages over 14 days differently
        message = self.params.get('message_id')
        if message:
            delta = datetime.now(timezone.utc) - Snowflake(int(message)).created_at
            params += f'?{1 if delta > timedelta(days=14) else 0}'

        return params


class RateLimiter(Protocol):
    """Lockkeeper taking care of respecting rate limits."""

    def __init__(self) -> None: ...

    def get(self, route: Route) -> Lock:
        """Get a lock by the route about to be made a request towards.

        The implementation of this function should handle several endpoints
        having the same X-RateLimit-Bucket, after the request is made the
        `update()` method will be called with the X-RateLimit-Bucket header so
        that the ratelimiter has a chance to fill this cache.
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
    locks: WeakValueDictionary[str, RateLimit]
    fallbacks: Dict[str, RateLimit]

    __slots__ = ('global_event', 'buckets', 'locks', 'fallbacks')

    def __init__(self) -> None:
        # Global ratelimit lock
        self.global_event = asyncio.Event()
        self.global_event.set()

        self.buckets: Dict[str, str] = {}  # Route endpoint to X-RateLimit-Bucket

        # By using a WeakValueDictionary, Python can deallocate locks if
        # they're not in any way used (waiting, or acquired). This way we
        # don't have to deal with any form of LRU structure.
        # This is important as each bucket + major parameters gets a lock in
        # this dictionary, even if you only send one request.
        self.locks: WeakValueDictionary[str, RateLimit] = WeakValueDictionary()

        # Fallback locks before buckets get populated
        self.fallbacks: Dict[str, RateLimit] = {}

    def default(self, mapping: MutableMapping[str, RateLimit], key: str) -> RateLimit:
        """Get `key` from the mapping, if it isn't found initialize a RateLimit in its place."""
        lock = mapping.get(key)
        if not lock:
            lock = RateLimit(self.global_event)
            mapping[key] = lock

        return lock

    def get(self, route: Route) -> RateLimit:
        """Get a lock by the route about to be made a request towards."""
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
