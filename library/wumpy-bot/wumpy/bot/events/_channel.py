import dataclasses
from datetime import datetime, timezone
from typing import ClassVar, FrozenSet, Optional

from discord_typings import (
    ChannelPinsUpdateData, ThreadCreateData, ThreadDeleteData,
    ThreadListSyncData, ThreadUpdateData, TypingStartData
)
from typing_extensions import Literal, Self
from wumpy.models import Member, Snowflake, Thread, ThreadMember

from .._dispatch import Event
from .._utils import _get_as_snowflake, backport_slots

__all__ = (
    'TypingEvent',
    'ChannelPinsUpdateEvent',
)


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
    def from_payload(
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
class ThreadCreateEvent(Event):
    thread: Thread

    newly_created: bool

    NAME: ClassVar[str] = "THREAD_CREATE"

    @classmethod
    def from_payload(
            cls,
            payload: ThreadCreateData,
            cached: None = None
    ) -> Self:
        return cls(
            thread=Thread.from_data(payload),
            newly_created=payload.get('newly_created', False)
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ThreadUpdateEvent(Event):
    thread: Thread
    cached: Optional[Thread]

    NAME: ClassVar[str] = "THREAD_UPDATE"

    @classmethod
    def from_payload(
            cls,
            payload: ThreadUpdateData,
            cached: Optional[Thread] = None
    ) -> Self:
        return cls(
            thread=Thread.from_data(payload),
            cached=cached
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ThreadDeleteEvent(Event):
    thread_id: Snowflake
    parent_id: Snowflake
    guild_id: Snowflake
    type: Literal[10, 11, 12]

    cached: Optional[Thread]

    NAME: ClassVar[str] = "THREAD_DELETE"

    @classmethod
    def from_payload(
            cls,
            payload: ThreadDeleteData,
            cached: Optional[Thread] = None
    ) -> Self:
        return cls(
            thread_id=Snowflake(payload['id']),
            parent_id=Snowflake(payload['parent_id']),
            guild_id=Snowflake(payload['guild_id']),
            type=payload['type'],
            cached=cached
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ThreadListSyncEvent(Event):
    guild_id: Snowflake
    channel_ids: FrozenSet[Snowflake]

    threads: FrozenSet[Thread]
    thread_members: FrozenSet[ThreadMember]

    NAME: ClassVar[str] = "THREAD_LIST_SYNC"

    @classmethod
    def from_payload(
            cls,
            payload: ThreadListSyncData,
            cached: None = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            channel_ids=frozenset([
                Snowflake(channel_id) for channel_id in payload.get('channel_ids', ())
            ]),
            threads=frozenset([Thread.from_data(thread) for thread in payload['threads']]),
            thread_members=frozenset([
                ThreadMember.from_data(thread_member)
                for thread_member in payload['members']
            ]),
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
    def from_payload(
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
