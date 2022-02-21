import dataclasses
from datetime import datetime, timedelta
from typing import Literal, Optional, Tuple

from discord_typings import (
    CategoryChannelData, DMChannelData, PartialChannelData, TextChannelData,
    ThreadChannelData, ThreadMemberData, VoiceChannelData
)
from typing_extensions import Self

from .base import Model, Snowflake
from .permissions import PermissionOverwrite, Permissions
from .user import User
from .utils import _get_as_snowflake

__all__ = (
    'PartialChannel', 'InteractionChannel', 'DMChannel', 'VoiceChannel',
    'TextChannel', 'NewsChannel', 'Category'
)


@dataclasses.dataclass(frozen=True, eq=False)
class PartialChannel(Model):
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

    @classmethod
    def from_data(cls, data: PartialChannelData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
        )


@dataclasses.dataclass(frozen=True, eq=False)
class InteractionChannel(PartialChannel):
    """Channel with only a handful of fields.

    An instance of this class is passed in interactions. The `permissions`
    attribute defaults a Permission object with no fields set.

    Attributes:
        permissions: The permissions for the user who invoked the interaction.
    """

    permissions: Permissions

    __slots__ = ('permissions',)

    @classmethod
    def from_data(cls, data: PartialChannelData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            permissions=Permissions(int(data.get('permissions', 0)))
        )


@dataclasses.dataclass(frozen=True, eq=False)
class DMChannel(Model):

    type: Literal[1]

    recipients: Tuple[User, ...]
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: Optional[datetime]

    @classmethod
    def from_data(cls, data: DMChannelData) -> Self:
        last_pin_timestamp = data.get('last_pin_timestamp')
        if last_pin_timestamp is not None:
            last_pin_timestamp = datetime.fromisoformat(last_pin_timestamp)

        return cls(
            id=int(data['id']),
            type=data['type'],

            recipients=tuple(User.from_data(d) for d in data['recipients']),
            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
        )


@dataclasses.dataclass(frozen=True, eq=False)
class TextChannel(PartialChannel):

    type: Literal[0]

    guild_id: Optional[Snowflake]
    parent_id: Optional[Snowflake]

    position: int
    overwrites: Tuple[PermissionOverwrite, ...]
    topic: Optional[str]
    nsfw: bool
    slowmode_delay: int

    last_message_id: Optional[Snowflake]
    last_pin_timestamp: Optional[datetime]
    default_auto_archive: Optional[timedelta]

    @classmethod
    def from_data(cls, data: TextChannelData) -> Self:
        last_pin_timestamp = data.get('last_pin_timestamp')
        if last_pin_timestamp is not None:
            last_pin_timestamp = datetime.fromisoformat(last_pin_timestamp)

        auto_archive_duration = data.get('default_auto_archive_duration')
        if auto_archive_duration is not None:
            auto_archive_duration = timedelta(seconds=auto_archive_duration)

        overwrites = tuple(
            PermissionOverwrite.from_data(d) for d in data['permission_overwrites']
        )

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            guild_id=_get_as_snowflake(data, 'guild_id'),
            parent_id=_get_as_snowflake(data, 'parent_id'),

            position=data['position'],
            overwrites=overwrites,
            topic=data['topic'],
            nsfw=data['nsfw'],
            slowmode_delay=data['rate_limit_per_user'],

            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
            default_auto_archive=auto_archive_duration
        )


@dataclasses.dataclass(frozen=True, eq=False)
class NewsChannel(TextChannel):

    Literal[5]

    @classmethod
    def from_data(cls, data: TextChannelData) -> Self:
        last_pin_timestamp = data.get('last_pin_timestamp')
        if last_pin_timestamp is not None:
            last_pin_timestamp = datetime.fromisoformat(last_pin_timestamp)

        auto_archive_duration = data.get('default_auto_archive_duration')
        if auto_archive_duration is not None:
            auto_archive_duration = timedelta(seconds=auto_archive_duration)

        overwrites = tuple(
            PermissionOverwrite.from_data(d) for d in data['permission_overwrites']
        )

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            guild_id=_get_as_snowflake(data, 'guild_id'),

            position=data['position'],
            overwrites=overwrites,
            topic=data['topic'],
            nsfw=data['nsfw'],
            slowmode_delay=data['rate_limit_per_user'],

            parent_id=_get_as_snowflake(data, 'parent_id'),
            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
            default_auto_archive=auto_archive_duration
        )


@dataclasses.dataclass(frozen=True, eq=False)
class ThreadMember:
    id: Optional[int]
    user_id: Optional[int]
    joined_at: datetime
    flags: int

    @classmethod
    def from_data(cls, data: ThreadMemberData) -> Self:
        id = data.get('id')
        user = data.get('user_id')

        return cls(
            id=int(id) if id is not None else None,
            user_id=int(user) if user is not None else None,
            joined_at=datetime.fromisoformat(data['join_timestamp']),
            flags=data['flags'],
        )


@dataclasses.dataclass(frozen=True, eq=False)
class ThreadChannel(PartialChannel):

    type: Literal[10, 11, 12]

    guild_id: Optional[Snowflake]
    parent_id: Optional[Snowflake]
    owner_id: Snowflake

    message_count: int
    member_count: int

    archived: bool
    auto_archive_delay: int
    locked: bool
    invitable: bool

    thread_member: Optional[ThreadMember]
    slowmode_delay: int

    last_message_id: Optional[Snowflake]
    last_pin_timestamp: Optional[datetime]

    @classmethod
    def from_data(cls, data: ThreadChannelData) -> Self:
        metadata = data['thread_metadata']

        thread_member = data.get('thread_member')
        if thread_member is not None:
            thread_member = ThreadMember.from_data(thread_member)

        last_pin_timestamp = data.get('last_pin_timestamp')
        if last_pin_timestamp is not None:
            last_pin_timestamp = datetime.fromisoformat(last_pin_timestamp)

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            guild_id=_get_as_snowflake(data, 'guild_id'),
            parent_id=_get_as_snowflake(data, 'parent_id'),
            owner_id=Snowflake(int(data['owner_id'])),

            message_count=data['message_count'],
            member_count=data['member_count'],

            archived=metadata['archived'],
            auto_archive_delay=metadata['auto_archive_duration'],
            locked=metadata['locked'],
            invitable=metadata.get('invitable', True),

            thread_member=thread_member,
            slowmode_delay=data['rate_limit_per_user'],

            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
        )


@dataclasses.dataclass(frozen=True, eq=False)
class VoiceChannel(PartialChannel):

    type: Literal[2, 13]

    guild_id: Optional[Snowflake]
    parent_id: Optional[Snowflake]

    position: int
    overwrites: Tuple[PermissionOverwrite, ...]
    nsfw: bool
    bitrate: int
    user_limit: int
    rtc_region: Optional[str]

    @classmethod
    def from_data(cls, data: VoiceChannelData) -> Self:
        overwrites = tuple(
            PermissionOverwrite.from_data(d) for d in data['permission_overwrites']
        )

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            guild_id=_get_as_snowflake(data, 'guild_id'),
            parent_id=_get_as_snowflake(data, 'parent_id'),

            position=data['position'],
            overwrites=overwrites,
            nsfw=data['nsfw'],
            bitrate=data['bitrate'],
            user_limit=data['user_limit'],
            rtc_region=data['rtc_region'],

        )


@dataclasses.dataclass(frozen=True, eq=False)
class Category(PartialChannel):

    type: Literal[4]

    guild_id: Optional[Snowflake]

    position: int
    overwrites: Tuple[PermissionOverwrite, ...]
    nsfw: bool

    @classmethod
    def from_data(cls, data: CategoryChannelData) -> Self:
        overwrites = tuple(
            PermissionOverwrite.from_data(d) for d in data['permission_overwrites']
        )

        return cls(
            id=int(data['id']),
            name=data['name'],
            type=data['type'],
            guild_id=_get_as_snowflake(data, 'guild_id'),

            position=data['position'],
            overwrites=overwrites,
            nsfw=data['nsfw'],
        )
