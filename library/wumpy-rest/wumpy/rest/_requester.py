from abc import ABC, abstractmethod
from contextvars import ContextVar, Token
from types import TracebackType
from typing import (
    IO, Any, Dict, Mapping, Optional, Sequence, Tuple, Type, Union
)

from typing_extensions import Self

from ._route import Route
from ._utils import MISSING

__all__ = (
    'Requester',
)


_current_api: ContextVar['Requester'] = ContextVar('_current_api')

# The following type variables are adapted from HTTPX because of a conversion
# done from a RequestFiles -> HTTPXFiles (the latter which HTTPX understands)
FileContent = Union[IO[bytes], bytes]
RequestFiles = Sequence[FileContent]
HTTPXFiles = Union[Mapping[str, FileContent], Sequence[Tuple[str, FileContent]]]


class Requester(ABC):
    """Base for making requests to Discord's API, respecting ratelimits.

    This is meant to be re-used for many different purposes and as such does
    not contain any actual routes or implementation. An actual implementation
    of `Requester` *must* provide a `request()` method.

    Use it as an asynchronous context manager to ensure that sockets and tasks
    are properly cleaned up.
    """

    _opened: bool
    _prev_context: Optional[Token]

    __slots__ = ('_opened', '_prev_context')

    # If this method would not take arbitrary args and kwargs, then subclasses
    # would technically violate the signature
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._opened = False
        self._prev_context = None

    async def __aenter__(self) -> Self:
        if self._opened:
            raise RuntimeError("Cannot enter already opened requester")

        self._opened = True
        self._prev_context = _current_api.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None
    ) -> None:
        self._opened = False

        # There should be an old token, but this is not the place to complain
        if self._prev_context is not None:
            _current_api.reset(self._prev_context)

    @staticmethod
    def _clean_dict(mapping: Dict[Any, Any]) -> Dict[Any, Any]:
        """Clean a dictionary from MISSING values.

        Returned is a new dictionary with only the keys not having a
        MISSING value left.
        """
        return {k: v for k, v in mapping.items() if v is not MISSING}

    @abstractmethod
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
        ...
