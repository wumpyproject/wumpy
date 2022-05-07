from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Optional, Tuple

from typing_extensions import Self
from wumpy.models import Snowflake
from wumpy.models.member import Member

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
    member: Optional[Member]

    NAME: ClassVar[str] = "TYPING_START"

    __slots__ = ('user_id', 'channel_id', 'guild_id', 'timestamp', 'member')

    @classmethod
    async def from_payload(
            cls,
            payload: Dict[str, Any],
            cached: Tuple[Optional[Any], Optional[Any]] = (None, None)
    ) -> Self:
        data = payload['d']
        cache = get_bot().cache

        user_id = Snowflake(data['user_id'])
        guild_id = _get_as_snowflake(data, 'guild_id')

        member = None
        if guild_id is not None and not cache.remote:
            member = await get_bot().cache.get_member(guild_id.id, user_id.id)

        if member is None:
            user = None
            if not cache.remote:
                user = await get_bot().cache.get_user(data['user_id'])

            if user is not None:
                member = Member.from_user(user, data['member'])
            else:
                member = Member.from_data(data['member'])

        return cls(
            user_id=user_id,
            channel_id=Snowflake(data['channel_id']),
            guild_id=guild_id,

            timestamp=datetime.fromtimestamp(data['timestamp'], tz=timezone.utc),
            member=member
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
            payload: Dict[str, Any],
            cached: Tuple[Optional[Any], Optional[Any]] = (None, None)
    ) -> Self:
        data = payload['d']

        last_pin = None
        if data.get('last_pin_timestamp') is not None:
            last_pin = datetime.fromisoformat(data['last_pin_timestamp'])

        return cls(
            channel_id=Snowflake(int(payload['d']['channel_id'])),
            guild_id=_get_as_snowflake(data, 'guild_id'),
            last_pin_timestamp=last_pin
        )
