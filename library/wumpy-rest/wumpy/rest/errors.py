from typing import Any, Dict, Optional, Union

from httpx import Response

__all__ = ('HTTPException', 'Forbidden', 'NotFound', 'ServerException')


class HTTPException(Exception):
    """Exception that all HTTP related exceptions originate from.

    The exceptions are smartly inherited in the following schema:
    ```
    HTTPException
    └── RequestException
        ├── Forbidden
        ├── NotFound
        └── ServerException
    ```
    """
    pass


class RequestException(HTTPException):
    """Exception subclassed by exceptions relating to failed requests."""

    response: Response
    data: Union[str, Dict, None]

    errors: Optional[Dict[str, Any]]
    message: str
    code: int

    def __init__(self, response: Response, data: Union[str, Dict, None] = None) -> None:
        if isinstance(data, dict):
            message = data.get('message', '')
            code = data.get('code', 0)

            errors = data.get('errors')
        else:
            message = ''
            code = 0
            errors = None

        self.response = response
        self.data = data

        self.errors = errors
        self.message = message
        self.code = code

        super().__init__(
            '{0.status_code} {0.reason_phrase} (Discord error code: {1}) {2}'.format(
                self.response, self.code, self.message
            )
        )


class Forbidden(RequestException):
    """Exception raised when the requester hits a 403 response."""
    pass


class NotFound(RequestException):
    """Exception raised when the requester hits a 404 response."""
    pass


class ServerException(RequestException):
    """Exception raised when the requester hits a 500 range response."""
    pass
