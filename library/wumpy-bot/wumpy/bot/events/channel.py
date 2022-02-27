from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..models import Snowflake
from ..utils import Event, _get_as_snowflake

__all__ = ('TypingEvent', 'ChannelPinsUpdateEvent')


class TypingEvent(Event):
    """Dispatched when a user starts typing in a channel."""

    user_id: Snowflake
    channel_id: Snowflake
    guild_id: Optional[Snowflake]

    timestamp: datetime
    member: Optional[Dict[str, Any]]

    NAME = "TYPING_START"

    __slots__ = ('user_id', 'channel_id', 'guild_id', 'timestamp', 'member')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.user_id = Snowflake(data['d']['user_id'])
        self.channel_id = Snowflake(data['d']['channel_id'])
        self.guild_id = _get_as_snowflake(data['d'], 'guild_id')

        self.timestamp = datetime.fromtimestamp(data['d']['timestamp'], tz=timezone.utc)
        self.member = data['d'].get('member')


class ChannelPinsUpdateEvent(Event):
    """Dispatched when a channel's pins are updated.

    Discord sends this event when the pins of a channel is updated, either when
    a message is pinned or unpinned.

    Deleting a pinned message does not count as unpinning it; Discord does not
    send this event when a pinned message is deleted.
    """

    channel_id: Snowflake
    last_pin_timestamp: Optional[datetime]

    NAME = "CHANNEL_PINS_UPDATE"

    __slots__ = ('channel_id', 'last_pin_timestamp')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.channel_id = Snowflake(data['d']['channel_id'])

        timestamp = data['d'].get('last_pin_timestamp')
        if timestamp:
            self.last_pin_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            self.last_pin_timestamp = None
