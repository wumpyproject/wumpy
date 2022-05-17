from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Literal, Optional, Tuple

from discord_typings import TypingStartData
from discord_typings.gateway import ChannelPinsUpdateData
from typing_extensions import Self
from wumpy.models import Member, Snowflake, User

from ..bot import get_bot
from ..dispatch import Event
from ..utils import _get_as_snowflake

__all__ = ('TypingEvent', 'ChannelPinsUpdateEvent')


@dataclass(frozen=True)
class TypingEvent(Event):
    """Dispatched when a user starts typing in a channel."""

    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    timestamp: datetime

    user: Optional[User]
    member: Optional[Member]

    NAME: ClassVar[str] = "TYPING_START"

    __slots__ = ('user_id', 'channel_id', 'guild_id', 'timestamp', 'member')

    @classmethod
    async def from_payload(
            cls,
            payload: TypingStartData,
            cached: Tuple[Optional[Any], Optional[Any]] = (None, None)
    ) -> Self:
        cache = get_bot().cache

        user_id = Snowflake(payload['user_id'])
        guild_id = _get_as_snowflake(payload, 'guild_id')

        user = None
        if not cache.remote:
            user = await cache.get_user(payload['user_id'])

        member = None
        if guild_id is not None and not cache.remote:
            member = await cache.get_member(guild_id.id, user_id.id)

        member_data = payload.get('member')
        if member is None and member_data is not None:
            if user is not None:
                member = Member.from_user(user, member_data)
            else:
                member = Member.from_data(member_data)

            # The user data may have been inside of the member object. If it
            # wasn't - and user is currently None - we would've gotten an error
            # and this code won't run.
            if user is None:
                user = member.user

        return cls(
            user_id=user_id,
            channel_id=Snowflake(payload['channel_id']),
            guild_id=guild_id,

            timestamp=datetime.fromtimestamp(payload['timestamp'], tz=timezone.utc),

            user=user,
            member=member,
        )


@dataclass(frozen=True)
class ChannelPinsUpdateEvent(Event):
    """Dispatched when a channel's pins are updated.

    Discord sends this event when the pins of a channel is updated, either when
    a message is pinned or unpinned.

    Deleting a pinned message does not count as unpinning it; Discord does not
    send this event when a pinned message is deleted.
    """

    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    last_pin_timestamp: Optional[datetime]

    NAME: ClassVar[str] = "CHANNEL_PINS_UPDATE"

    __slots__ = ('channel_id', 'guild_id', 'last_pin_timestamp')

    @classmethod
    async def from_payload(
            cls,
            payload: ChannelPinsUpdateData,
            cached: Tuple[Optional[Any], Optional[Any]] = (None, None)
    ) -> Self:

        last_pin = payload.get('last_pin_timestamp')
        if last_pin is not None:
            last_pin = datetime.fromisoformat(last_pin)

        return cls(
            channel_id=Snowflake(int(payload['channel_id'])),
            guild_id=_get_as_snowflake(payload, 'guild_id'),
            last_pin_timestamp=last_pin
        )
