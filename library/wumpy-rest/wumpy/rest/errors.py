from typing import Any, Dict, Mapping, Optional, Union

from httpx import codes

__all__ = ('HTTPException', 'Forbidden', 'NotFound', 'ServerException')


class HTTPException(Exception):
    """Base for all HTTP exceptions.

    The exceptions are smartly inherited in the following schema:

        HTTPException
        └── RequestException
            ├── Forbidden
            ├── NotFound
        └── ServerException
    """

    __slots__ = ()


class RequestException(HTTPException):
    """Exception subclassed by exceptions relating to failed requests.

    Attributes:
        status_code: The HTTP status code of the response.
        status_phrase: The phrase that goes along with the status code.
        headers: The headers returned by the response.
        data: The body of the response (possibly None).
        errors: The errors returned by Discord in the body.
        message: The message returned by Discord in the body.
        code: The error code returned by Discord in the body.
        attempt:
            The number of times the request has been attempted, this should be
            used to implement exponential backoff in the Ratelimiter.
    """

    status_code: int
    status_phrase: str
    headers: Mapping[str, str]

    data: Union[str, Dict[str, Any], None]

    errors: Optional[Dict[str, Any]]
    message: str
    code: int

    attempt: int

    __slots__ = (
        'status_code', 'status_phrase', 'headers', 'data', 'errors',
        'message', 'code', 'attempt'
    )

    def __init__(
        self,
        status_code: int,
        headers: Mapping[str, str],
        data: Union[str, Dict[str, Any], None] = None,
        *,
        attempt: int = 0
    ) -> None:
        if isinstance(data, dict):
            message = data.get('message', '')
            code = data.get('code', 0)

            errors = data.get('errors')
        else:
            message = ''
            code = 0
            errors = None

        self.status_code = status_code
        self.status_phrase = codes.get_reason_phrase(self.status_code)
        self.headers = headers

        self.data = data

        self.errors = errors
        self.message = message
        self.code = code

        self.attempt = attempt

        super().__init__(
            '{0.status_code} {0.status_phrase} (Discord error code: {1}) {2}'.format(
                self, code, message
            )
        )


class RateLimited(RequestException):
    """Exception raised when the client is being rate limited."""

    __slots__ = ()


class Forbidden(RequestException):
    """Exception raised when the requester hits a 403 response."""

    __slots__ = ()


class NotFound(RequestException):
    """Exception raised when the requester hits a 404 response."""

    __slots__ = ()


class ServerException(RequestException):
    """Exception raised when the requester hits a 500 range response."""

    __slots__ = ()
