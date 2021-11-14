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
from typing import TYPE_CHECKING, Any
from typing import Deque as DequeType
from typing import Dict, List, Optional, Sequence, SupportsInt, Tuple, overload

from ..utils import MISSING, File
from .base import Object, Snowflake
from .flags import AllowedMentions
from .permissions import PermissionOverwrite, Permissions, PermissionTarget

if TYPE_CHECKING:
    from ..gateway import RESTClient
    from .user import User


__all__ = (
    'PartialChannel', 'InteractionChannel', 'ChannelHistory',
    'DMChannel', 'VoiceChannel', 'TextChannel', 'NewsChannel',
)


class PartialChannel(Object):
    """Channel with only a handful of fields.

    This is passed in interactions and invites.

    Attributes:
        name: The name of the channel.
        type: The type of the channel.
    """

    name: str
    type: int

    __slots__ = ('name', 'type')

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.name = data['name']
        self.type = data['type']


class InteractionChannel(PartialChannel):
    """Channel with only a handful of fields.

    An instance of this class is passed in interactions. The `permissions`
    attribute defaults a Permission object with no fields set.

    Attributes:
        permissions: The permissions for the user who invoked the interaction.
    """

    permissions: Permissions

    __slots__ = ('permissions',)

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

        self.permissions = Permissions(int(data.get('permissions', 0)))


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
        messages = self._rest.fetch_messages(
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


class SendableChannel:
    """Discord text-based channel that you can message.

    This is an incomplete-mixin that should not be used on its own.
    """

    id: int  # Resolved by classes inherting the mixin

    __slots__ = ()

    # Satisfy type checkers who don't know that this class
    # will be subclassed with Object in the future
    def __int__(self) -> int:
        return self.id

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
        # All Discord objects should first be wrapped in models before making
        # them stateful.
        raise NotImplementedError  # TODO

        return await self._rest.send_message(
            self, content=content, tts=tts, embeds=embeds,
            allowed_mentions=allowed_mentions, file=file, stickers=stickers
        )

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel."""
        raise NotImplementedError  # TODO

        await self._rest.trigger_typing(self.id)

    async def fetch_message(self, id: int) -> Dict[str, Any]:
        """Fetch a single message from the channel."""
        raise NotImplementedError  # TODO

        return await self._rest.fetch_message(self, id)

    async def edit_message(
        self,
        id: int,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        file: Optional[File] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        attachments: Optional[Dict[str, Any]] = MISSING
    ) -> Dict[str, Any]:
        """Edit a message the bot sent in a message."""
        raise NotImplementedError  # TODO

        return await self._rest.edit_message(
            self, id,
            content=content, embeds=embeds, file=file,
            allowed_mentions=allowed_mentions, attachments=attachments
        )

    async def delete_message(self, id: int, *, reason: str = MISSING) -> None:
        """Delete a message sent in the channel."""
        raise NotImplementedError  # TODO

        await self._rest.delete_message(self, id, reason=reason)

    async def bulk_delete_messages(self, messages: List[SupportsInt], *, reason: str = MISSING) -> None:
        """Bulk delete several messages in the channel."""
        raise NotImplementedError  # TODO

        await self._rest.bulk_delete_messages(self, messages, reason=reason)

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
        raise NotImplementedError  # TODO

        if around and (limit is None or limit > 100):
            raise TypeError("'limit' cannot be over 100 or None when 'around' is set")

        return ChannelHistory(
            self._rest, self, before=before, after=after,
            around=around, limit=limit
        )

    async def fetch_pins(self) -> List[Dict[str, Any]]:
        """Fetch all pinned messages in a channel."""
        raise NotImplementedError  # TODO

        return await self._rest.fetch_pins(self)

    async def delete(self, *, reason: str = MISSING) -> None:
        """Delete the channel."""
        raise NotImplementedError  # TODO

        await self._rest.delete_channel(self, reason=reason)


class DMChannel(Object, SendableChannel):
    """Discord DM channel object with a user."""

    last_message_id: Snowflake
    recipient: 'User'

    __slots__ = ('last_message_id', 'recipient')

    def __init__(self, data: Dict[str, Any]) -> None:
        self._update(data)

    def _update(self, data: Dict) -> None:
        self.last_message_id = Snowflake(int(data['last_message_id']))

        # Even though Discord sends an array of user object, bots cannot
        # participate in group DMs so it will only have 1 item
        user_data = data['recipients'][0]
        from .user import User  # Circular imports
        recipient = User(user_data)

        self.recipient = recipient


class GuildChannel(Object):
    """Channel attached to a guild."""

    __slots__ = ()

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

    async def set_permission(
        self,
        overwrite: PermissionOverwrite,
        type: Optional[PermissionTarget] = None,
        *,
        reason: str = MISSING
    ) -> None:
        """Edit a permission overwrite."""
        # The plan is to wrap all objects, then make them stateful.
        raise NotImplementedError  # TODO

        if type is None and overwrite.type is None:
            raise TypeError("'type' not set in PermissionOverwrite object or arguments")

        assert type is not None and overwrite.type is not None  # Pyright bug

        await self._rest.set_permission(
            self, overwrite.id,
            allow=int(overwrite.allow), deny=int(overwrite.deny),
            type=type or overwrite.type, reason=reason
        )

    async def delete_permission(self, target: SupportsInt, *, reason: str = MISSING) -> None:
        """Delete a channel permission overwrite."""
        raise NotImplementedError  # TODO

        await self._rest.delete_permission(self, target, reason=reason)


class VoiceChannel(GuildChannel):
    """Discord voice channel allowing voice calls."""
    pass


class TextChannel(GuildChannel, SendableChannel):
    """Discord Text channel in a guild."""
    pass


class NewsChannel(GuildChannel, SendableChannel):
    """Discord News channel."""
    pass
