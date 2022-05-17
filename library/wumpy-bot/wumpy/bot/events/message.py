import dataclasses
from typing import ClassVar, FrozenSet, Optional, Sequence, Tuple

from discord_typings import (
    MessageCreateData, MessageDeleteBulkData, MessageDeleteData,
    MessageReactionAddData, MessageReactionRemoveData,
    MessageReactionRemoveEmojiData, MessageUpdateData
)
from typing_extensions import Self
from wumpy.models import Emoji, Member, Message, Snowflake

from ..bot import get_bot
from ..dispatch import Event
from ..utils import _get_as_snowflake, backport_slots

__all__ = (
    'MessageDeleteEvent', 'BulkMessageDeleteEvent', 'ReactionAddEvent', 'ReactionRemoveEvent',
    'ReactionClearEvent', 'ReactionEmojiClearEvent'
)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class MessageCreateEvent(Event):
    message: Message

    NAME: ClassVar[str] = 'MESSAGE_CREATE'

    @classmethod
    async def from_payload(
            cls,
            payload: MessageCreateData,
            cached: Tuple[None, Optional[Message]] = (None, None)
    ) -> Self:
        if cached[1] is None:
            message = Message.from_data(payload)
        else:
            message = cached[1]

        return cls(message=message)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class MessageUpdateEvent(Event):
    message: Message
    cached: Optional[Message]

    NAME: ClassVar[str] = 'MESSAGE_UPDATE'

    @classmethod
    async def from_payload(
            cls,
            payload: MessageUpdateData,
            cached: Tuple[Optional[Message], Optional[Message]] = (None, None)
    ) -> Self:
        if cached[1] is None:
            message = Message.from_data(payload)
        else:
            message = cached[1]

        return cls(message=message, cached=cached[0])


@backport_slots()
@dataclasses.dataclass(frozen=True)
class MessageDeleteEvent(Event):
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    cached: Optional[Message]

    NAME: ClassVar[str] = "MESSAGE_DELETE"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageDeleteData,
            cached: Tuple[Optional[Message], None] = (None, None)
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            cached=cached[0]
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class BulkMessageDeleteEvent(Event):
    """Dispatched when multiple messages are deleted at once."""

    message_ids: FrozenSet[Snowflake]
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    cached: Optional[FrozenSet[Message]]

    NAME: ClassVar[str] = "MESSAGE_DELETE_BULK"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageDeleteBulkData,
            cached: Tuple[Optional[Sequence[Message]], None] = (None, None)
    ) -> Self:
        return cls(
            message_ids=frozenset([Snowflake(id_) for id_ in payload['ids']]),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            cached=frozenset(cached[0]) if cached[0] is not None else None
        )


@backport_slots()
@dataclasses.dataclass()
class ReactionAddEvent(Event):
    """Dispatched when a user adds a reaction to a message."""

    message_id: Snowflake
    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Emoji
    member: Optional[Member]

    NAME: ClassVar[str] = "MESSAGE_REACTION_ADD"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageReactionAddData,
            cached: Tuple[None, None] = (None, None)
    ) -> Self:
        cache = get_bot().cache

        user_id = Snowflake(payload['user_id'])
        guild_id = _get_as_snowflake(payload, 'guild_id')

        member = None
        member_data = payload.get('member')
        if member_data is not None:
            user = None
            if not cache.remote:
                member = await cache.get_member(guild_id, user_id)
                if member is None:
                    user = await cache.get_user(user_id)

            if member is None:
                if user is not None:
                    # We can re-use the User object already in-memory from the
                    # cache we looked up
                    member = Member.from_user(user, member_data)
                else:
                    member = Member.from_data(member_data)

        return cls(
            message_id=Snowflake(payload['message_id']),
            user_id=user_id,
            channel_id=Snowflake(payload['channel_id']),
            guild_id=guild_id,

            emoji=Emoji.from_data(payload['emoji']),
            member=member,
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ReactionRemoveEvent(Event):
    """Dispatched when a reaction is removed from a message."""

    message_id: Snowflake
    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Emoji

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageReactionRemoveData,
            cached: Tuple[None, None] = (None, None)
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['message_id']),
            user_id=Snowflake(payload['user_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            emoji=Emoji.from_data(payload['emoji'])
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ReactionClearEvent(Event):
    """Dispatched when all reactions is removed from a message."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE_ALL"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageDeleteData,
            cached: Tuple[None, None] = (None, None)
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ReactionEmojiClearEvent(Event):
    """Dispatched when only a specific emoji's reactions are cleared."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Emoji

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE_EMOJI"

    @classmethod
    async def from_payload(
            cls,
            payload: MessageReactionRemoveEmojiData,
            cached: Tuple[None, None] = (None, None)
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['message_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            emoji=Emoji.from_data(payload['emoji'])
        )
