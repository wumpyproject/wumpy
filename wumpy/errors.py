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

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from httpx import Response

if TYPE_CHECKING:
    from .interactions.base import CommandInteraction


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


class ConnectionClosed(WumpyException):
    """Exception raised when the WebSocket to the Discord gateway was closed."""
    pass


class CommandException(WumpyException):
    """Parent for all exceptions raised regarding command handlers."""
    pass


class CommandSetupError(CommandException):
    """Raised when local command setup does not align with interactions.

    Examples of this is incorrect types of local options compared to what
    Discord sends, or subcommand-groups not receiving subcommands.
    """
    pass


class CommandNotFound(CommandSetupError):
    """Raised when no local command handler can be found for an interaction."""

    interaction: 'CommandInteraction'
    command: str

    def __init__(self, interaction: 'CommandInteraction', command: str) -> None:
        super().__init__(f"Command handler for '{command}' not found")

        self.interaction = interaction
        self.command = command
