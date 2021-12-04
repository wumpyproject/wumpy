import contextlib
import sys
from datetime import datetime, timezone
from pkg_resources import get_distribution
from types import TracebackType
from typing import Any, Callable, Coroutine, Dict, Optional, Tuple, Type, Union
from urllib.parse import quote as urlquote

import httpx
import anyio
import anyio.abc
from typing_extensions import Self

from ..errors import (
    Forbidden, HTTPException, NotFound, RequestException, ServerException
)
from ..utils import MISSING, load_json, dump_json
from .locks import RateLimit
from .ratelimiter import DictRateLimiter, RateLimiter, Route

__all__ = ('build_user_agent', 'Requester')


def build_user_agent() -> str:
    """Build a User-Agent to use in making requests."""

    v = get_distribution('wumpy.rest').version

    agent = f'DiscordBot (https://github.com/Bluenix2/wumpy, version: {v})'
    agent += f" Python/{'.'.join([str(i) for i in sys.version_info])}"

    return agent


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


class Requester:
    """Base for making requests to Discord's API, respecting ratelimits.

    This is meant to be re-used for many different purposes and as such does
    not contain any actual routes.

    Use it as an asynchronous context manager to ensure that sockets and tasks
    are properly cleaned up.
    """

    headers: Dict[str, str]

    ratelimiter: RateLimiter

    _session: httpx.AsyncClient

    __slots__ = ('headers', 'ratelimiter', '_session', '_tasks', '_stack')

    def __init__(self, ratelimiter=DictRateLimiter, *, headers: Dict[str, str] = {}) -> None:
        # Headers global to the requester
        self.headers: Dict[str, str] = {
            'User-Agent': build_user_agent(),
            'X-RateLimit-Precision': 'millisecond',
            **headers,
        }

        self.ratelimiter = ratelimiter()

    async def __aenter__(self) -> Self:
        if hasattr(self, '_stack'):
            raise RuntimeError("Cannot enter already opened requester")

        self._stack = contextlib.AsyncExitStack()

        try:
            self._tasks = await self._stack.enter_async_context(anyio.create_task_group())
            self._session = await self._stack.enter_async_context(
                httpx.AsyncClient(headers=self.headers, http2=True, follow_redirects=True)
            )
        except:
            # If any of the __aenter__s fails in the above block the finalizer
            # won't be called correctly. This is important to handle if we get
            # cancelled for example..
            await self._stack.__aexit__(*sys.exc_info())
            raise

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        await self._stack.__aexit__(exc_type, exc_val, traceback)

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
        """Sleep through a 429 Too Many Requests response.

        This method simply sleeps the amount specified in the response, locking
        the global ratelimit lock if necessary.

        Parameters:
            data: The JSON deserialized body of the response.
        """
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
        auth: Optional[Tuple[Union[str, bytes], Union[str, bytes]]] = None
    ) -> Optional[Any]:
        """Make one attempt at a successful request.

        Parameters:
            route: The route to make the request to.
            headers: Headers to use when making the request.
            ratelimit: Ratelimit lock for this route.
            attempt: How many attempts have been made at this route.
            json: Dictionary to serialize to JSON and send as the request body.
            data: Dictionary to send as a multipart form-data request body.
            auth:
                Tuple with two items: (username, password) to authorize with
                using BASIC. This parameter is not used, as Discord primarily
                authenticates using the Authorization header.

        Raises:
            Forbidden: The request received a 403 Forbidden response.
            NotFound: The request received a 404 Not Found response.
            ServerException:
                The request received a 503 Service Unavailable response, this
                is different from 500, 502 or 504 responses as they are
                gracefully retried.
            HTTPException:
                The request received a non-successful unknown response. Simply
                indicates a general failure.

        Returns:
            The JSON deserialized body of the response, or None if the request
            was unsuccessful and should be retried.
        """
        content = dump_json(json) if json is not None else None

        res = await self.session.request(
            route.method, route.url,
            headers={'Content-Type': 'application/json', **headers},
            content=content, data=data, auth=auth
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
            await res.aclose()
            await anyio.sleep(1 + attempt * 2)
            return None

        elif res.status_code in {403, 404, 503}:
            # Normally called when the response body is fully called, since we
            # don't read the body here we need to call it manually.
            await res.aclose()

            if res.status_code == 403:
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

        # We're being ratelimited by Discord
        if res.status_code == 429:
            if not isinstance(data, dict):
                # This should not happen, but there is a possibility since
                # data is not always a dict. We could potentially look at the
                # response headers, but for now the best course of action seems
                # to
                await anyio.sleep(1 + attempt * 2)
                return None

            # Returning None will cause the function to try again
            return await self._handle_ratelimit(data)

        raise HTTPException(
            f'Unknown response {res.status_code} {res.reason_phrase}:', data
        )

    async def request(self, route: Route, *, reason: str = MISSING, **kwargs: Any) -> Any:
        """Send a request to the Discord API, respecting rate limits.

        If the `json` keyword-argument contains values that are MISSING,
        they will be removed before being passed to HTTPX.

        This function returns a deserialized JSON object if Content-Type is
        `application/json`, otherwise a string. Commonly it is known by the
        caller itself what the response will be, in which case it will be
        a burden to narrow down the type unneccesarily. For that reason this
        function is annotated as returning `Any`.

        Parameters:
            route: The route to make the request to.
            reason:
                The reason to insert into the Audit Log for this change, not
                supported by all endpoints.
            headers: Headers to use when making the request.
            ratelimit: Ratelimit lock for this route.
            attempt: How many attempts have been made at this route.
            json: Dictionary to serialize to JSON and send as the request body.
            data: Dictionary to send as a multipart form-data request body.
            auth:
                Tuple with two items: (username, password) to authorize with
                using BASIC. This parameter is not used, as Discord primarily
                authenticates using the Authorization header.

        Raises:
            Forbidden: The request received a 403 Forbidden response.
            NotFound: The request received a 404 Not Found response.
            ServerException:
                The request received a 503 Service Unavailable response, this
                is different from 500, 502 or 504 responses as they are
                gracefully retried.
            HTTPException:
                The request received a non-successful unknown response. Simply
                indicates a general failure, can also be raised if no attempt
                at the request was successful.

        Returns:
            The JSON deserialized body of the response, or None if the request
            was unsuccessful and should be retried.
        """

        # Clean up MISSING values
        if 'json' in kwargs:
            kwargs['json'] = self._clean_dict(kwargs['json'])

        # Create the headers for the request
        headers: Dict[str, str] = kwargs.pop('headers', {})

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

        raise HTTPException(f'All attempts at {route} were unsuccessful.')

    async def _bypass_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> bytes:
        """Bypass retrying, ratelimit handling and json serialization.

        The point of this function is to make a "raw" request somewhere.
        Commonly to a CDN endpoint, that does not have ratelimits and needs to
        read the bytes.

        Parameters:
            method: The HTTP method to use.
            url: The URL to make the request to.
            kwargs: Keyword arguments to pass to HTTPX.

        Returns:
            The response body read as bytes.
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
        """Read the bytes of a CDN asset.

        Parameters:
            url: The full URL to the asset.
            size: The value of the 'size' query parameter.

        Returns:
            The CDN asset read as bytes.
        """
        return await self._bypass_request('GET', url, params={'size': size})
