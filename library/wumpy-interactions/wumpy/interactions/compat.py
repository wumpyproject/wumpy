import json
from typing import (
    TYPE_CHECKING, Any, Awaitable, Callable, Dict, Mapping, Optional, overload
)

from typing_extensions import Protocol

try:
    from sanic import HTTPResponse  # type: ignore
    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False

if TYPE_CHECKING:
    from sanic import Request as OriginalSanicRequest

__all__ = ('Request', 'ASGIRequest', 'SanicRequest')


class Request(Protocol):

    @overload
    async def respond(
        self,
        data: Optional[Mapping[str, Any]] = None,
        *,
        status: int = 200,
    ) -> None:
        ...

    @overload
    async def respond(
        self,
        *,
        status: int = 200,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> None:
        ...


class ASGIRequest(Request):
    def __init__(
            self,
            scope: Dict[str, Any],
            receive: Callable[[], Awaitable[Dict[str, Any]]],
            send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        self._responded = False

        self.scope = scope
        self.receive = receive
        self.send = send

    async def respond(
        self,
        data: Optional[Mapping[str, Any]] = None,
        *,
        status: int = 200,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> None:
        if (
            data is None and body is None
            or data is not None and body is not None
        ):
            raise TypeError("'respond()' has to be called with one of 'data' and 'body'")

        if self._responded:
            raise RuntimeError('Response has already been sent')

        if data is not None:
            body = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if content_type is None:
            content_type = 'text/plain'

        await self.send({
            'type': 'http.response.start', 'status': status,
            'headers': [(b'content-type', content_type.encode('utf-8'))]
        })
        await self.send({'type': 'http.response.body', 'body': body})


class SanicRequest(Request):
    def __init__(self, request: 'OriginalSanicRequest') -> None:
        self._responded = False

        self.request = request

    async def respond(
        self,
        data: Optional[Mapping[str, Any]] = None,
        *,
        status: int = 200,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> None:
        if (
            data is None and body is None
            or data is not None and body is not None
        ):
            raise TypeError("'respond()' has to be called with one of 'data' and 'body'")

        if self._responded:
            raise RuntimeError('Response has already been sent')

        if data is not None:
            body = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if content_type is None:
            content_type = 'text/plain'

        await self.request.respond(HTTPResponse(
            body, status=status, content_type=content_type
        ))
