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

from typing import Any, Dict, Optional, Type

from ..models import DMChannel, User
from .rest import RESTClient

__all__ = ('Cache',)


class Cache:
    """Keeping track of the cache and memory state of the library."""

    _rest: 'RESTClient'

    _users: Dict[int, User]
    _channels: Dict[int, DMChannel]

    __slots__ = ('_rest', '_users', '_channels')

    def __init__(self, rest: 'RESTClient') -> None:
        self._rest = rest

        self._users = {}
        self._channels = {}

    def store_user(self, data: Dict[str, Any], *, cls: Type[User] = User) -> User:
        """Create and store a user in an internal cache.

        This method is also used to update an existing user.
        """
        existing = self._users.get(int(data['id']))
        if existing:
            existing._update(data)
            return existing

        new = cls(self._rest, data)
        self._users[new.id] = new
        return new

    def get_user(self, id: int) -> Optional[User]:
        """Get a user object from cache."""
        return self._users.get(id)

    def store_channel(self, data: Dict[str, Any], *, cls: Type[DMChannel] = DMChannel) -> DMChannel:
        """Create and store a channel in the internal cache.

        Additionally, if a channel is found, it is updated with the new data.
        """
        existing = self._channels.get(int(data['id']))
        if existing:
            existing._update(data)
            return existing

        new = cls(self._rest, self, data)
        self._channels[new.id] = new
        return new

    def get_channel(self, id: int) -> Optional[DMChannel]:
        """Get a channel from cache."""
        return self._channels.get(id)
