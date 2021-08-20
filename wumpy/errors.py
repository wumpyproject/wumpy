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

from typing import Any, Dict, Optional, Union

from aiohttp import ClientResponse

__all__ = (
    'WumpyException', 'HTTPException', 'Forbidden',
    'NotFound', 'ServerException'
)


class WumpyException(Exception):
    """Base exception that all other exceptions from the library subclass."""
    pass


class HTTPException(WumpyException):
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


class RequestException(WumpyException):
    """Exception subclassed by exceptions relating to failed requests."""

    response: ClientResponse
    data: Union[str, Dict, None]

    errors: Optional[Dict[str, Any]]
    message: str
    code: int

    def __init__(self, response: ClientResponse, data: Union[str, Dict, None] = None) -> None:
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
            '{0.status} {0.reason} (Discord error code: {1})'.format(
                self.response, self.code
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
