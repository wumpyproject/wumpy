import dataclasses
from datetime import datetime, timezone
from typing import ClassVar, Optional

from discord_typings import ChannelPinsUpdateData, TypingStartData
from typing_extensions import Self
from wumpy.models import Member, Snowflake

from ..dispatch import Event
from ..utils import _get_as_snowflake, backport_slots

__all__ = ('TypingEvent', 'ChannelPinsUpdateEvent')


@backport_slots()
@dataclasses.dataclass(frozen=True)
class TypingEvent(Event):
    """Dispatched when a user starts typing in a channel."""

    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    timestamp: datetime
    member: Optional[Member]

    NAME: ClassVar[str] = "TYPING_START"

    @classmethod
    async def from_payload(
            cls,
            payload: TypingStartData,
            cached: None = None
    ) -> Self:
        member = None
        if 'member' in payload:
            member = Member.from_data(payload['member'])

        return cls(
            user_id=Snowflake(payload['user_id']),
            channel_id=Snowflake(payload['channel_id']),
            guild_id=_get_as_snowflake(payload, 'guild_id'),

            timestamp=datetime.fromtimestamp(payload['timestamp'], tz=timezone.utc),
            member=member,
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
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

    @classmethod
    async def from_payload(
            cls,
            payload: ChannelPinsUpdateData,
            cached: None = None
    ) -> Self:
        last_pin = payload.get('last_pin_timestamp')
        if last_pin is not None:
            last_pin = datetime.fromisoformat(last_pin)

        return cls(
            channel_id=Snowflake(int(payload['channel_id'])),
            guild_id=_get_as_snowflake(payload, 'guild_id'),
            last_pin_timestamp=last_pin
        )
