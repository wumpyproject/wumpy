import collections
import contextlib
from typing import Iterable, Optional, Tuple, List, Dict, Any, Deque, SupportsInt, overload

import anyio.lowlevel
from discord_typings import PartialChannelData, MessageData
from discord_typings.resources.channel import ChannelData, DMChannelData
from typing_extensions import Self
from wumpy.rest import Forbidden

from .utils import STATELESS, MISSING, _get_as_snowflake
from .base import Object, Snowflake
from .permissions import Permissions, PermissionOverwrite, PermissionTarget

__all__ = (
    'PartialChannel', 'InteractionChannel', 'ChannelHistory',
    'DMChannel', 'VoiceChannel', 'TextChannel', 'NewsChannel',
)


class PartialChannel(Object):
    """Channel with only a handful of fields.

    This is passed in interactions and invites because Discord sends extremely
    limited data about the channels.

    Attributes:
        id: The ID of the channel.
        name: The name of the channel.
        type: The type of the channel.
    """

    name: str
    type: int

    __slots__ = ('name', 'type')

    def __init__(self, data: PartialChannelData) -> None:
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

    def __init__(self, data: PartialChannelData) -> None:
        super().__init__(data)

        self.permissions = Permissions(int(data.get('permissions', 0)))


class ChannelHistory:
    """Iterator and awaitable object representing Discord message history.

    This allows you to iterate over the messages in a channel or fetch them all
    at once. Use the `history()` methods on the channels to get an instance of
    this class - it is not meant to be instantiated directly.
    """

    channel: SupportsInt
    messages: Deque[MessageData]

    before: int
    after: int
    around: int

    limit: Optional[int]

    __slots__ = ('api', 'channel', 'messages', 'before', 'after', 'around', 'limit')

    def __init__(
        self,
        api,
        channel: SupportsInt,
        *,
        before: int = MISSING, after: int = MISSING, around: int = MISSING,
        limit: Optional[int] = 50,
    ) -> None:
        self.api = api

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

    async def fetch(self, *, batch: bool = False) -> List[MessageData]:
        """Fetch another batch of messages from the channel.

        Because of the way Discord limits the amount of messages that can be
        fetched at once, with a big enough `limit` not all messages will be
        returned with one method call. Therefore, if `limit` is over 100 or
        None this method should be called until it returns an empty list.

        Parameters:
            batch:
                A keyword argument that must be passed if `limit` is None or
                over 100. Without this argument, an error will be raised
                warning the user that this method must be called several times.

        Raises:
            TypeError: `batch` is not passed when batching is necessary.

        Returns:
            A list of messages returned by the API, could be empty to signal
            that it shouldn't be called again.
        """
        if self.limit is None or self.limit > 100 and batch is False:
            raise TypeError(
                "Expected 'batch' to be True when limit set to None or over"
                "100 (method must be batched)"
            )

        self.limit, amount = self.calculate_amount(self.limit, 100)

        if self.limit == 0 and amount == 0:
            await anyio.lowlevel.checkpoint()
            return []

        # We have to ignore the types here because we don't want to add
        # an overload that accepts all kwargs
        messages = self.api.fetch_messages(
            self.channel, before=self.before,
            after=self.after, around=self.around,
            limit=amount
        )  # type: ignore

        if self.after and messages:
            self.after = int(messages[-1]['id'])
        elif self.before and messages:
            self.before = int(messages[0]['id'])

        if len(messages) != amount:
            self.limit = 0

        return messages

    def __await__(self):
        return self.fetch().__await__()

    async def __anext__(self) -> MessageData:
        """Fetch the next message from the channel.

        Because Discord allows fetching multiple messages, there is a potential
        that all this method does is pop from an internal deque.

        Returns:
            The next message from the channel according to the options
            configured.
        """
        if self.messages:
            message = self.messages.popleft()
            await anyio.lowlevel.checkpoint()
            return message

        if self.limit is not None and self.limit <= 0:
            raise StopAsyncIteration()

        self.messages.extend(await self.fetch())

        if not self.messages:
            # The API has no more messages to give us
            raise StopAsyncIteration()

        return self.messages.popleft()


class SendableChannel(Object):
    """Discord text-based channel that you can message.

    The point of this class is to be a shared mixin for all models that have
    the ability to send messages to them.
    """

    __slots__ = ('api',)

    def __init__(self, data: ChannelData, *, api=STATELESS) -> None:
        super().__init__(int(data['id']))

        self.api = api

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
        """Trigger a typing indicator in the channel.

        The indicator will trigger for a few seconds until a message is sent,
        meaning that it does not last until you somehow stop it.

        Officially Discord does not recommend bots to implement this endpoint,
        it should only rarely be called if something is expected to take a few
        seconds to compute or send.

        During an elevated usage during one of Facebook's downtimes Discord
        disabled this endpoint for a few hours through Cloudflare, causing it
        to return a 403 Forbidden error. In anticipation for similar events,
        this method **will supress `Forbidden` errors** as this endpoint is
        considered non-vital.
        """
        with contextlib.suppress(Forbidden):
            await self.api.trigger_typing(self)

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

    async def delete_message(self, id: SupportsInt, *, reason: str = MISSING) -> None:
        """Delete a message sent in the channel.

        If the message was not sent by the bot-user this endpoint requires the
        `MANAGE_MESSAGES` permission to execute.

        Parameters:
            id: The ID of the message to delete.
            reason: The audit log reason for deleting the message.
        """
        await self.api.delete_message(self, int(id), reason=reason)

    async def bulk_delete_messages(
        self,
        messages: Iterable[SupportsInt],
        *,
        reason: str = MISSING
    ) -> None:
        """Bulk delete several messages in the channel.

        If the message was not sent by the bot-user this endpoint requires the
        `MANAGE_MESSAGES` permission to execute.

        Parameters:
            messages: The IDs of the messages to delete.
        """

        await self.api.bulk_delete_messages(self, [int(m) for m in messages], reason=reason)

    @overload
    def history(self, *, before: SupportsInt, limit: Optional[int] = 50) -> ChannelHistory:
        ...

    @overload
    def history(self, *, after: SupportsInt, limit: Optional[int] = 50) -> ChannelHistory:
        ...

    @overload
    def history(self, *, around: SupportsInt, limit: int = 50) -> ChannelHistory:
        # Neither behaviour possible would be satisfactory for having an
        # unlimited limit for 'around'. The most expected behaviour would
        # probably be to continue from the last message but then you don't get
        # an even distribution of messages before the snowflake, and after.
        ...

    def history(
        self,
        *,
        before: SupportsInt = MISSING,
        after: SupportsInt = MISSING,
        around: SupportsInt = MISSING,
        limit: Optional[int] = 50
    ) -> ChannelHistory:
        """Fetch the message history of the channel.

        Because of how `around` works, the library can't handle a limit
        over 100 to make multiple requests. This function returns a special
        ChannelHistory object that can be awaited, or used with `async for`.
        If `limit` is set to None then all messages will be iterated through.

        Parameters:
            before: Snowflake to fetch messages before.
            after: Snowflake to fetch messages around.
            around:
                Snowflake to fetch messages around. `limit` cannot be larger
                than 100 or None when this is used.
            limit:
                The amount of messages to fetch. Discord only allows fetching
                100 messages, the library will automatically fetch more in
                multiple batches if necessary. None indicates unlimited.

        Returns:
            A special `ChannelHistory` object that can be awaited or used in an
            `async for` loop to iterate through all messages.
        """

        if around and (limit is None or limit > 100):
            raise TypeError("'limit' cannot be over 100 or None when 'around' is set")

        return ChannelHistory(
            self.api, self,
            before=int(before), after=int(after), around=int(around),
            limit=limit
        )

    async def fetch_pins(self) -> List[Dict[str, Any]]:
        """Fetch all pinned messages in a channel."""
        raise NotImplementedError  # TODO

        return await self._rest.fetch_pins(self)

    async def delete(self, *, reason: str = MISSING) -> Self:
        """Delete the channel.

        For guilds this requires the `MANAGE_CHANNELS` permission or
        `MANAGE_THREADS` depending on the type of channel. Important to note is
        that deleting categories does not delete its children.

        Parameters:
            reason: The audit log reason for deleting the channel.

        Returns:
            A new channel object, with the most up-to-date data returned from
            Discord.
        """

        return self.__class__(await self.api.delete_channel(self, reason=reason), api=self.api)


class DMChannel(SendableChannel):
    """Discord DM channel object with a user."""

    last_message_id: Optional[Snowflake]
    recipient: 'User'

    __slots__ = ('last_message_id', 'recipient')

    def __init__(self, data: DMChannelData, *, api=STATELESS) -> None:
        super().__init__(data, api=api)

        self.last_message_id = _get_as_snowflake(data, 'last_message_id')

        # Even though Discord sends an array of user object, bots cannot
        # participate in group DMs so it will only have 1 item
        from .user import User  # Circular imports
        self.recipient = User(data['recipients'][0], api=api)


class GuildChannel(Object):
    """Channel attached to a guild."""

    __slots__ = ('api',)

    def __init__(self, data: Dict[str, Any], *, api=STATELESS) -> None:
        super().__init__(int(data['id']))

        self.api = api

    async def set_permission(
        self,
        overwrite: PermissionOverwrite,
        type: Optional[PermissionTarget] = None,
        *,
        reason: str = MISSING
    ) -> None:
        """Edit a permission overwrite on a channel.

        The `MANAGE_ROLES` permission is required for this endpoint, and only
        permissions that the bot has in the guild or channel can be changed.

        Parameters:
            overwrite: The new, overriden, permission overwrite.
            type:
                The type of target, only applies if it isn't set in the
                PermissionOverwrite object.
            reason: The audit log reason for changing the permission.
        """
        if type is None and overwrite.type is None:
            raise TypeError("'type' not set in PermissionOverwrite object or arguments")

        await self.api.set_permission(
            self, overwrite.id,
            allow=int(overwrite.allow), deny=int(overwrite.deny),
            type=type or overwrite.type, reason=reason
        )

    async def delete_permission(self, target: SupportsInt, *, reason: str = MISSING) -> None:
        """Delete a channel permission overwrite.

        This endpoint requires the bot-user to have the `MANAGE_ROLES`
        permission.

        Permissions:
            target: The ID of the target to delete.
            reason: The audit log reason for deleting the overwrite.
        """

        await self.api.delete_permission(self, target, reason=reason)


class VoiceChannel(GuildChannel):
    """Discord voice channel allowing voice calls."""
    pass


class TextChannel(GuildChannel, SendableChannel):
    """Discord Text channel in a guild."""
    pass


class NewsChannel(GuildChannel, SendableChannel):
    """Discord News channel."""
    pass
