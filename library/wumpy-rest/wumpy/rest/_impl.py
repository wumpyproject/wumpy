import contextlib
import logging
import sys
from types import TracebackType
from typing import (
    Any, Awaitable, Callable, Dict, Mapping, Optional, Tuple, Type, TypeVar,
    Union, cast, overload
)
from urllib.parse import quote as urlquote

import anyio
import anyio.abc
import httpx
from typing_extensions import Self

from . import endpoints
from ._config import RatelimiterContext
from ._errors import (
    Forbidden, HTTPException, NotFound, RateLimited, RequestException,
    ServerException
)
from ._ratelimiter import DictRatelimiter, Ratelimiter
from ._requester import HTTPXFiles, Requester, _current_api
from ._route import Route
from ._utils import MISSING, dump_json, load_json

__all__ = (
    'HTTPXRequester',
    'APIClient',
    'get_api',
)

_log = logging.getLogger(__name__)
T = TypeVar('T')


class HTTPXRequester(Requester):

    _session: httpx.AsyncClient
    _ratelimiter: Ratelimiter
    _stack: contextlib.AsyncExitStack

    __slots__ = (
        '_ratelimiter', '_session', '_stack', '_base_url',
    )

    def __init__(
        self,
        token: Optional[str] = None,
        *,
        headers: Dict[str, str] = {},
        ratelimiter: Optional[Ratelimiter] = None,
        base_url: str = 'https://discord.com/api/v10',
        proxy: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        super().__init__()

        self._stack = contextlib.AsyncExitStack()

        default_headers = {'User-Agent': self.build_user_agent()}
        if token is not None:
            default_headers['Authorization'] = f'Bot {token}'

        self._session = httpx.AsyncClient(
            headers={**default_headers, **headers},
            proxies=proxy, follow_redirects=True, timeout=timeout
        )
        self._ratelimiter = ratelimiter if ratelimiter is not None else DictRatelimiter()
        self._base_url = base_url

    async def __aenter__(self) -> Self:
        await super().__aenter__()

        try:
            await self._stack.enter_async_context(self._session)
            await self._stack.enter_async_context(self._ratelimiter)
        except BaseException:
            # If any of the __aenter__s fails in the above block the finalizer
            # won't be called correctly. This is important to handle if we get
            # cancelled for example..
            await self._stack.__aexit__(*sys.exc_info())
            self._opened = False
            raise

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        try:
            await self._stack.__aexit__(exc_type, exc_val, traceback)
        finally:
            await super().__aexit__(exc_type, exc_val, traceback)

    @property
    def session(self) -> httpx.AsyncClient:
        if not hasattr(self, '_session'):
            raise RuntimeError("'session' attribute accessed before connection opened")

        return self._session

    @staticmethod
    def build_user_agent() -> str:
        """Build a User-Agent to use in making requests.

        If `wumpy-rest` is used to build another library, this method should be
        overriden so that Discord receives metrics for this library. Please do
        not do so otherwise as it messes with Discord's metrics.

        Returns:
            The value for the `User-Agent` header field.
        """

        agent = 'DiscordBot (https://github.com/wumpyproject/wumpy, version: 0.0.1)'
        agent += f" Python/{'.'.join([str(i) for i in sys.version_info])}"

        return agent

    async def _request(
        self,
        route: Route,
        headers: Dict[str, str],
        ratelimit: Callable[[Mapping[str, str]], Awaitable[object]],
        *,
        json: Optional[Any] = None,
        data: Optional[Dict[Any, Any]] = None,
        files: Optional[HTTPXFiles] = None,
        params: Optional[Dict[str, Any]] = None,
        auth: Optional[Tuple[Union[str, bytes], Union[str, bytes]]] = None
    ) -> Optional[Any]:
        """Make one attempt at a successful request.

        Parameters:
            route: The route to make the request to.
            headers: Headers to use when making the request.
            ratelimit: Ratelimit lock for this route.
            json: Dictionary to serialize to JSON and send as the request body.
            data: Dictionary to send as a multipart form-data request body.
            files: Additional files to include in the request.
            params: Query string parameters for the request.
            auth:
                Tuple with two items: (username, password) to authorize with
                using BASIC. This parameter is not often used, as Discord
                primarily authenticates using the Authorization header.

        Raises:
            Forbidden: The request received a 403 Forbidden response.
            NotFound: The request received a 404 Not Found response.
            ServerException:
                The request received a 500, 502, 503 or 504 response.
            Ratelimited: The request received a 429 Too Many Requests response.
            HTTPException:
                The request received a non-successful unknown response. Simply
                indicates a general failure.

        Returns:
            The JSON deserialized body of the response, or None if the request
            was unsuccessful and should be retried.
        """
        if json is not None:
            content = dump_json(json)
            headers = {'Content-Type': 'application/json', **headers}
        else:
            content = None

        res = await self.session.request(
            route.method, self._base_url + route.url,
            headers=headers, content=content, data=data, files=files, auth=auth, params=params
        )

        # Update rate limit information if we have received it, as well as do
        # any form of ratelimit handling.
        await ratelimit(res.headers)

        if res.status_code in {403, 404, 500, 502, 503, 504}:
            # Normally called when the response body is fully called, since we
            # don't read the body here we need to call it manually.
            await res.aclose()

            if res.status_code == 403:
                raise Forbidden(res.status_code, res.headers)
            elif res.status_code == 404:
                raise NotFound(res.status_code, res.headers)
            else:
                raise ServerException(res.status_code, res.headers)

        # The status code is now either 300> or >= 200 or 429
        text = (await res.aread()).decode(encoding='utf-8')

        # This is for the typing, because load_json returns Any and screws a
        # lot of things up..
        payload: Union[Dict[str, Any], str] = ''

        if res.headers.get('Content-Type') == 'application/json':
            payload = load_json(text)
        else:
            payload = text

        # Successful request
        if 300 > res.status_code >= 200:
            return payload

        # We're being ratelimited by Discord (or possibly Cloudflare)
        if res.status_code == 429:
            raise RateLimited(res.status_code, res.headers, payload)

        raise RequestException(res.status_code, res.headers, payload)

    async def request(
        self,
        route: Route,
        *,
        reason: str = MISSING,
        json: Optional[Any] = None,
        data: Optional[Dict[Any, Any]] = None,
        files: Optional[HTTPXFiles] = None,
        params: Optional[Dict[str, Any]] = None,
        auth: Optional[Tuple[Union[str, bytes], Union[str, bytes]]] = None,
        headers: Optional[Mapping[str, str]] = None
    ) -> Any:
        """Send a request to the Discord API, respecting rate limits.

        If the `json`, `data` or `params` keyword-arguments contains values
        that are MISSING, they will be removed before being passed to HTTPX.

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
            json: Dictionary to serialize to JSON and send as the request body.
            data: Dictionary to send as a multipart form-data request body.
            files: Additional files to include in the request.
            params: Query string parameters for the request.
            headers: Headers to use when making the request.
            auth:
                Tuple with two items: (username, password) to authorize with
                using BASIC. This parameter is not used, as Discord primarily
                authenticates using the Authorization header.
            headers: Headers to send in the request.

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
            The JSON deserialized body of the response.
        """

        # Clean up MISSING values
        if isinstance(json, dict):
            json = self._clean_dict(json)
        if data is not None:
            data = self._clean_dict(data)
        if params is not None:
            params = self._clean_dict(params)

        rheaders = dict(headers or {})
        if reason is not MISSING:
            rheaders['X-Audit-Log-Reason'] = urlquote(reason, safe='/ ')

        for attempt in range(3):
            async with self._ratelimiter(route, RatelimiterContext()) as rl:
                try:
                    res = await self._request(
                        route, rheaders, rl,
                        json=json, data=data, files=files, params=params,
                        auth=auth
                    )
                except httpx.RequestError as error:
                    if attempt < 3:
                        _log.warning(
                            f'Request to {route} failed with a HTTPX RequestError;'
                            f' retrying request (attempt {attempt}).'
                        )
                        # Exponentially backoff and try again
                        await anyio.sleep(1 + attempt * 2)
                        continue

                    # Even the last attempt failed, so we want to make sure it
                    # reaches the user.
                    raise error

                return res

            # If we reach here, that means that an exception happened and the
            # ratelimiter silenced it. It is up to the ratelimiter to log a
            # message with higher severity depending on the reason it did so.
            _log.info(f'Retrying request to {route} (attempt {attempt}).')

        raise HTTPException(f'All attempts at {route} were unsuccessful.')

    async def _bypass_request(
        self,
        method: str,
        url: str,
        *,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Bypass retrying, ratelimit handling and json serialization.

        The point of this function is to make a "raw" request somewhere.
        Commonly to a CDN endpoint, that does not have ratelimits and needs to
        read the bytes.

        Parameters:
            method: The HTTP method to use.
            url: The URL to make the request to.
            json: JSON body for the request.
            params: Query string parameters to use in the request.

        Returns:
            The response body read as bytes.
        """

        # Clean up MISSING values
        if json is not None:
            json = self._clean_dict(json)
        if params is not None:
            params = self._clean_dict(params)

        res = await self.session.request(method, url, json=json, params=params)

        if 300 > res.status_code >= 200:
            return await res.aread()

        if res.status_code == 403:
            raise Forbidden(res.status_code, res.headers)
        elif res.status_code == 404:
            raise NotFound(res.status_code, res.headers)
        elif res.status_code == 503:
            raise ServerException(res.status_code, res.headers)
        else:
            raise RequestException(res.status_code, res.headers)

    # Asset endpoint

    async def read_asset(self, url: str, *, size: int = MISSING) -> bytes:
        """Read the bytes of a CDN asset.

        Parameters:
            url: The full URL to the asset.
            size: The value of the 'size' query parameter.

        Returns:
            The CDN asset read as bytes.
        """
        return await self._bypass_request('GET', url, params={'size': size})


class APIClient(endpoints.ApplicationCommandEndpoints, endpoints.ChannelEndpoints,
                endpoints.GatewayEndpoints, endpoints.GuildEndpoints,
                endpoints.GuildTemplateEndpoints, endpoints.InteractionEndpoints,
                endpoints.StickerEndpoints, endpoints.UserEndpoints,
                endpoints.WebhookEndpoints, HTTPXRequester):
    """Requester class with all endpoints inherited and implemented."""

    __slots__ = ()


@overload
def get_api(*, verify: bool = False) -> APIClient:
    ...


@overload
def get_api(subclass: Type[T], *, verify: bool = False) -> T:
    ...


def get_api(subclass: Type[T] = APIClient, *, verify: bool = False) -> T:
    """Get the currently active API.

    This function is what powers `wumpy-models`'s ability to make API requests
    without passing an explicit API around.

    Parameters:
        subclass: The type of the return type for the type checker.
        verify: Whether to do an `isinstance()` check on the gotten instance.

    Raises:
        RuntimeError: There is no currently active API.
        RuntimeError: If `verify` is True, the `isinstance()` check failed

    Returns:
        The currently active API.
    """

    try:
        instance = _current_api.get()
    except LookupError:
        raise RuntimeError('There is no currently active API') from None

    if verify and not isinstance(instance, subclass):
        raise RuntimeError(f'Currently active API is not a subclass of {subclass.__name__!r}')

    return cast(T, instance)
