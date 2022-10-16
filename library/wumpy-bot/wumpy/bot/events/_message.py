from typing import ClassVar, FrozenSet, Optional, Sequence

import attrs
from discord_typings import (
    MessageCreateData, MessageDeleteBulkData, MessageDeleteData,
    MessageReactionAddData, MessageReactionRemoveData,
    MessageReactionRemoveEmojiData, MessageUpdateData
)
from typing_extensions import Self
from wumpy.models import Emoji, Member, Message, Snowflake

from .._dispatch import Event
from .._utils import _get_as_snowflake

__all__ = (
    'MessageDeleteEvent',
    'BulkMessageDeleteEvent',
    'ReactionAddEvent',
    'ReactionRemoveEvent',
    'ReactionClearEvent',
    'ReactionEmojiClearEvent',
)


@attrs.define(kw_only=True)
class MessageCreateEvent(Event):
    message: Message

    NAME: ClassVar[str] = 'MESSAGE_CREATE'

    @classmethod
    def from_payload(
            cls,
            payload: MessageCreateData,
            cached: None = None
    ) -> Self:
        return cls(message=Message.from_data(payload))


@attrs.define(kw_only=True)
class MessageUpdateEvent(Event):
    message: Message
    cached: Optional[Message]

    NAME: ClassVar[str] = 'MESSAGE_UPDATE'

    @classmethod
    def from_payload(
            cls,
            payload: MessageUpdateData,
            cached: Optional[Message] = None
    ) -> Self:
        return cls(message=Message.from_data(payload), cached=cached)


@attrs.define(kw_only=True)
class MessageDeleteEvent(Event):
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    cached: Optional[Message]

    NAME: ClassVar[str] = "MESSAGE_DELETE"

    @classmethod
    def from_payload(
            cls,
            payload: MessageDeleteData,
            cached: Optional[Message] = None
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            cached=cached
        )


@attrs.define(kw_only=True)
class BulkMessageDeleteEvent(Event):
    """Dispatched when multiple messages are deleted at once."""

    message_ids: FrozenSet[Snowflake]
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    cached: Optional[FrozenSet[Message]]

    NAME: ClassVar[str] = "MESSAGE_DELETE_BULK"

    @classmethod
    def from_payload(
            cls,
            payload: MessageDeleteBulkData,
            cached: Optional[Sequence[Message]] = None
    ) -> Self:
        return cls(
            message_ids=frozenset([Snowflake(id_) for id_ in payload['ids']]),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            cached=frozenset(cached) if cached is not None else None
        )


@attrs.define(kw_only=True)
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
    def from_payload(
            cls,
            payload: MessageReactionAddData,
            cached: None = None
    ) -> Self:
        member = None
        if 'member' in payload:
            member = Member.from_data(payload['member'])

        return cls(
            message_id=Snowflake(payload['message_id']),
            user_id=Snowflake(payload['user_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            emoji=Emoji.from_data(payload['emoji']),
            member=member,
        )


@attrs.define(kw_only=True)
class ReactionRemoveEvent(Event):
    """Dispatched when a reaction is removed from a message."""

    message_id: Snowflake
    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Emoji

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE"

    @classmethod
    def from_payload(
            cls,
            payload: MessageReactionRemoveData,
            cached: None = None
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['message_id']),
            user_id=Snowflake(payload['user_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            emoji=Emoji.from_data(payload['emoji'])
        )


@attrs.define(kw_only=True)
class ReactionClearEvent(Event):
    """Dispatched when all reactions is removed from a message."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE_ALL"

    @classmethod
    def from_payload(
            cls,
            payload: MessageDeleteData,
            cached: None = None
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),
        )


@attrs.define(kw_only=True)
class ReactionEmojiClearEvent(Event):
    """Dispatched when only a specific emoji's reactions are cleared."""

    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    emoji: Emoji

    NAME: ClassVar[str] = "MESSAGE_REACTION_REMOVE_EMOJI"

    @classmethod
    def from_payload(
            cls,
            payload: MessageReactionRemoveEmojiData,
            cached: None = None
    ) -> Self:
        return cls(
            message_id=Snowflake(payload['message_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            emoji=Emoji.from_data(payload['emoji'])
        )
