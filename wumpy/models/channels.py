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

import collections
from typing import (
    TYPE_CHECKING, Any, Deque as DequeType, Dict, List, Optional,
    Sequence, SupportsInt, Tuple, overload
)

from ..rest import File

from ..utils import MISSING
from .base import Object, Snowflake
from .flags import AllowedMentions

if TYPE_CHECKING:
    from ..state import Cache, RESTClient
    from .user import User


class ChannelHistory:
    """Iterator and awaitable object representing Discord message history."""

    _rest: 'RESTClient'
    channel: SupportsInt
    messages: DequeType

    before: int
    after: int
    around: int

    limit: Optional[int]

    __slots__ = ('_rest', 'channel', 'messages', 'before', 'after', 'around', 'limit')

    def __init__(
        self,
        rest: 'RESTClient',
        channel: SupportsInt,
        *,
        before: int = MISSING, after: int = MISSING, around: int = MISSING,
        limit: Optional[int] = 50
    ) -> None:
        self._rest = rest
        self.channel = channel
        self.messages = collections.deque()

        self.before = before
        self.after = after
        self.around = around

        self.limit = limit

    @staticmethod
    def calculate_amount(limit: Optional[int], chunk: int) -> Tuple[Optional[int], int]:
        """Calculate the amount of messages to fetch in the next request."""
        if limit is None:
            return None, chunk

        if limit >= chunk:
            return limit - chunk, chunk
        else:
            return 0, limit

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch a list of messages.

        Depending on how big the limit was set, this may require multiple
        calls. Eventually an empty list will be returned.
        """
        self.limit, amount = self.calculate_amount(self.limit, 100)

        # We have to ignore the types here because we don't want to add
        # an overload that accepts all kwargs
        messages = self._rest.fetch_channel_messages(
            self.channel, before=self.before,
            after=self.after, around=self.around,
            limit=amount
        )  # type: ignore

        if self.after and messages:
            self.after = int(messages[-1]['id'])
        elif self.before and messages:
            self.before = int(messages[0]['id'])

        return messages

    def __await__(self):
        return self.fetch().__await__()

    async def __anext__(self) -> Dict[str, Any]:
        try:
            return self.messages.popleft()
        except IndexError:
            if self.limit is not None and self.limit <= 0:
                raise StopAsyncIteration()

            self.messages.extend(await self.fetch())

            if not self.messages:
                # The API has no more messages to give us
                raise StopAsyncIteration()

            return self.messages.popleft()


class SendableChannel(Object):
    """Discord text-based channel that you can message."""

    _rest: 'RESTClient'

    __slots__ = ('_rest',)

    def __init__(self, rest: 'RESTClient', data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self._rest = rest

    def _update(self, data: Dict[str, Any]) -> None:
        pass

    async def send(
        self,
        content: str = MISSING,
        *,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
        stickers: Sequence[SupportsInt] = MISSING
    ) -> Dict[str, Any]:
        """Send a message to channel."""
        return await self._rest.send_message(
            self, content=content, tts=tts, embeds=embeds,
            allowed_mentions=allowed_mentions, file=file, stickers=stickers
        )

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel."""
        await self._rest.trigger_typing(self.id)

    async def fetch_message(self, id: int) -> Dict[str, Any]:
        """Fetch a single message from the channel."""
        return await self._rest.fetch_channel_message(self, id)

    @overload
    def history(self, *, before: int, limit: int = 50) -> ChannelHistory: ...

    @overload
    def history(self, *, after: int, limit: int = 50) -> ChannelHistory: ...

    @overload
    def history(self, *, around: int, limit: int = 50) -> ChannelHistory: ...

    @overload
    def history(self, *, before: int, limit: None) -> ChannelHistory: ...

    @overload
    def history(self, *, after: int, limit: None) -> ChannelHistory: ...

    def history(
        self,
        *,
        before: int = MISSING,
        after: int = MISSING,
        around: int = MISSING,
        limit: Optional[int] = 50
    ) -> ChannelHistory:
        """Fetch the message history of the channel.

        Because of how `around` works, the library can't handle a limit
        over 100 to make multiple requests. This function returns a special
        ChannelHistory object that can be awaited, or used with `async for`.
        If `limit` is set to None then all messages will be iterated through.
        """
        if around and (limit is None or limit > 100):
            raise TypeError("'limit' cannot be over 100 or None when 'around' is set")

        return ChannelHistory(
            self._rest, self, before=before, after=after,
            around=around, limit=limit
        )

    async def fetch_pins(self) -> List[Dict[str, Any]]:
        """Fetch all pinned messages in a channel."""
        return await self._rest.fetch_pins(self)

    async def delete(self, *, reason: str = MISSING) -> None:
        """Delete the channel."""
        data = await self._rest.delete_channel(self, reason=reason)
        self._update(data)


class DMChannel(SendableChannel):
    """Discord DM channel object with a user."""

    _cache: Optional['Cache']

    last_message_id: Snowflake
    recipient: 'User'

    __slots__ = ('_cache', 'last_message_id', 'recipient')

    def __init__(self, rest: 'RESTClient', cache: Optional['Cache'], data: Dict[str, Any]) -> None:
        super().__init__(rest, data)

        self._cache = cache

        self._update(data)

    def _update(self, data: Dict) -> None:
        self.last_message_id = Snowflake(int(data['last_message_id']))

        # Even though Discord sends an array of user object, bots cannot
        # participate in group DMs so it will only have 1 item
        user_data = data['recipients'][0]
        if self._cache:
            recipient = self._cache.store_user(user_data)
        else:
            from .user import User  # Circular imports
            recipient = User(self._rest, user_data)

        self.recipient = recipient
