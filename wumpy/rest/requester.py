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

import sys
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Callable, Coroutine, Dict, Optional, Type, TypeVar, Union
from urllib.parse import quote as urlquote

import httpx
import anyio
import anyio.abc

from ..errors import (
    Forbidden, HTTPException, NotFound, RequestException, ServerException
)
from ..utils import MISSING, load_json, dump_json
from .locks import RateLimit
from .ratelimiter import DictRateLimiter, RateLimiter, Route

__all__ = ('build_user_agent', 'Requester')


SELF = TypeVar('SELF', bound='Requester')


def build_user_agent() -> str:
    """Build a User-Agent to use in making requests."""
    from wumpy import __version__  # Avoid circular imports

    agent = f'DiscordBot (https://github.com/Bluenix2/wumpy, version: {__version__})'
    agent += f' Python/{sys.version_info[0]}.{sys.version_info[1]}'

    return agent


def releaser(delay: Union[int, float], callback: Callable) -> Callable[[], Coroutine]:
    """Coroutine function factory for sleeping and then call the callback."""
    async def inner(task_status: anyio.abc.TaskStatus = anyio.TASK_STATUS_IGNORED):
        task_status.started()
        try:
            await anyio.sleep(delay)
        finally:
            # The sleep could be cancelled and raise an exception, no matter
            # what we should call the callback and cleanup as to not leave
            # things in an invalid state.
            callback()
    return inner


class Requester:
    """A class to make requests against Discord's API, respecting ratelimits.

    This class itself does not actually contain any routes, that way it can be
    re-used and subclassed for several purposes.
    """

    headers: Dict[str, str]

    ratelimiter: RateLimiter

    _session: httpx.AsyncClient

    __slots__ = ('headers', 'ratelimiter', '_session', '_tasks')

    def __init__(self, ratelimiter=DictRateLimiter, *, headers: Dict[str, str] = {}) -> None:
        # Headers global to the requester
        self.headers: Dict[str, str] = {
            'User-Agent': build_user_agent(),
            'X-RateLimit-Precision': 'millisecond',
            **headers,
        }

        self.ratelimiter = ratelimiter()

    async def __aenter__(self: SELF) -> SELF:
        self._tasks = await anyio.create_task_group().__aenter__()
        self._session = await httpx.AsyncClient(http2=True).__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        await self._session.__aexit__(exc_type, exc_val, traceback)
        await self._tasks.__aexit__(exc_type, exc_val, traceback)

    @property
    def session(self) -> httpx.AsyncClient:
        if not hasattr(self, '_session'):
            raise RuntimeError("'session' attribute accessed before connection opened")

        return self._session

    @staticmethod
    def _clean_dict(mapping: Dict[Any, Any]) -> Dict[Any, Any]:
        """Clean a dictionary from MISSING values.

        Returned is a new dictionary with only the keys not having a
        MISSING value left.
        """
        return {k: v for k, v in mapping.items() if v is not MISSING}

    async def _handle_ratelimit(self, data: Dict[str, Any]) -> None:
        """Handle an unexpected 429 response."""
        retry_after: float = data['retry_after']

        is_global: bool = data.get('global', False)
        if is_global:
            self.ratelimiter.lock()  # Globally lock all requests

        await anyio.sleep(retry_after)

        if is_global:
            self.ratelimiter.unlock()  # Release now that the global ratelimit has passed

    async def _request(
        self,
        route: Route,
        headers: Dict[str, str],
        ratelimit: RateLimit,
        attempt: int,
        *,
        json: Optional[Any] = None,
        data: Optional[Dict] = None,
    ) -> Optional[Any]:
        """Attempt to actually make the request.

        None is returned if the request got a bad response which was handled
        and the function should be called again to retry.
        """
        content = dump_json(json) if json is not None else None

        res = await self.session.request(
            route.method, route.url,
            headers={'Content-Type': 'application/json', **headers},
            content=content, data=data
        )

        # Update rate limit information if we have received it
        self.ratelimiter.update(route, res.headers.get('X-RateLimit-Bucket'))

        if res.headers.get('X-RateLimit-Remaining') == '0':
            ratelimit.defer()

            reset = datetime.fromtimestamp(float(res.headers['X-Ratelimit-Reset']), timezone.utc)
            # Release later when the ratelimit resets
            self._tasks.start_soon(releaser(
                (reset - datetime.now(timezone.utc)).total_seconds(),
                ratelimit.release
            ))

        # No need to read the body for the following responses
        if res.status_code in {500, 502, 504}:
            await anyio.sleep(1 + attempt * 2)
            return None

        elif res.status_code == 403:
            raise Forbidden(res, data)
        elif res.status_code == 404:
            raise NotFound(res, data)
        elif res.status_code == 503:
            raise ServerException(res, data)

        # The status code is now either 300> or >= 200 or 429
        text = (await res.aread()).decode(encoding='utf-8')

        if res.headers.get('Content-Type') == 'application/json':
            body = load_json(text)
        else:
            body = text

        # Successful request
        if 300 > res.status_code >= 200:
            return body

        # Discord should be responding with a JSON body on a 429 response
        if not isinstance(data, dict):
            raise HTTPException(
                f'Unknown response {res.status_code} {res.reason_phrase}:', data
            )

        # We're being ratelimited by Discord
        if res.status_code == 429:
            # Returning None will cause the function to try again
            return await self._handle_ratelimit(data)

        raise RequestException(res, data)

    async def request(self, route: Route, *, reason: str = MISSING, **kwargs: Any) -> Any:
        """Make a request to the Discord API, respecting rate limits.

        If the `json` keyword-argument contains values that are MISSING,
        they will be removed before being passed to HTTPx.

        This function returns a deserialized JSON object if Content-Type is
        `application/json`, otherwise a string. Commonly it is known by the
        caller itself what the response will be, in which case it will be
        a burden to narrow down the type unneccesarily. For that reason this
        function is annotated as returning `Any`.
        """

        # Clean up MISSING values
        if 'json' in kwargs:
            kwargs['json'] = self._clean_dict(kwargs['json'])

        # Create the headers for the request
        headers: dict[str, str] = kwargs.pop('headers', {})

        # The second part of the if-statement is to check if the value is
        # truthy, otherwise we'll send an X-Audit-Log-Reason of None
        if reason is not MISSING:
            headers['X-Audit-Log-Reason'] = urlquote(reason, safe='/ ')

        for attempt in range(5):
            async with await self.ratelimiter.get(route) as rl:
                try:
                    res = await self._request(route, headers, rl, attempt, **kwargs)
                except OSError as error:
                    # Connection reset by peer
                    if attempt < 4 and error.errno in (54, 10054):
                        # Exponentially backoff and try again
                        await anyio.sleep(1 + attempt * 2)
                        continue

                    # The last attempt or some other error
                    raise error

                if res is None:
                    continue  # Something went wrong, let's retry

                return res

        raise HTTPException(f'All attempts at {route} failed')

    async def _bypass_request(
        self,
        method: str,
        url: str,
        *args,
        **kwargs
    ) -> bytes:
        """Bypass retrying, ratelimit handling and json serialization.

        The point of this function is to make a "raw" request somewhere.
        Commonly to a CDN endpoint, that does not have ratelimits and needs to
        read the bytes.
        """
        res = await self.session.request(method, url, **kwargs)

        if 300 > res.status_code >= 200:
            return await res.aread()

        if res.status_code == 403:
            raise Forbidden(res)
        elif res.status_code == 404:
            raise NotFound(res)
        elif res.status_code == 503:
            raise ServerException(res)
        else:
            raise RequestException(res)

    # Asset endpoint

    async def read_asset(self, url: str, *, size: int) -> bytes:
        return await self._bypass_request('GET', url, params={'size': size})
