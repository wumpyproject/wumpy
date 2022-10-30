from dataclasses import MISSING
from datetime import datetime
from typing import Optional, SupportsInt, Tuple

import attrs
from discord_typings import DMChannelData, ThreadChannelData
from typing_extensions import Literal, Self

from .._raw import (
    RawCategory, RawDMChannel, RawTextChannel, RawThread, RawThreadMember,
    RawVoiceChannel
)
from .._utils import MISSING, Snowflake, _get_as_snowflake, get_api
from . import _message, _user  # Circular imports


@attrs.define(eq=False)
class DMChannel(RawDMChannel):
    recipients: Tuple[_user.User, ...]

    @classmethod
    def from_data(cls, data: DMChannelData) -> Self:
        last_pin_timestamp = data.get('last_pin_timestamp')
        if last_pin_timestamp is not None:
            last_pin_timestamp = datetime.fromisoformat(last_pin_timestamp)

        return cls(
            id=int(data['id']),
            type=data['type'],

            recipients=tuple(_user.User.from_data(d) for d in data['recipients']),
            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
        )


@attrs.define(eq=False)
class TextChannel(RawTextChannel):
    ...


@attrs.define(eq=False)
class ThreadMember(RawThreadMember):
    ...


@attrs.define(eq=False)
class Thread(RawThread):
    thread_member: Optional[ThreadMember] = None

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
            slowmode_delay=data['rate_limit_per_user'],

            invitable=metadata.get('invitable', True),
            thread_member=thread_member,

            last_message_id=_get_as_snowflake(data, 'last_message_id'),
            last_pin_timestamp=last_pin_timestamp,
        )


@attrs.define(eq=False)
class VoiceChannel(RawVoiceChannel):
    ...


@attrs.define(eq=False)
class Category(RawCategory):
    ...
