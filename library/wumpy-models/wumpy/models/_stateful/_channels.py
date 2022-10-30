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

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel.

        In general, this endpoint should **not** be used by bots. Only if
        something may take a few seconds should this be used to let the user
        know that it is being processed.
        """
        await get_api().trigger_typing(self.id)

    async def pin_message(self, message: SupportsInt, *, reason: str = MISSING) -> None:
        """Pin a specific message in the channel.

        This method requires the `MANAGE_MESSAGES` permission. The maximum
        amount of pinned messages is 50.

        Parameters:
            message: The message or ID to pin.
            reason: The audit log reason for pinning the message.
        """
        await get_api().pin_message(self.id, message, reason=reason)


    async def unpin_message(self, message: SupportsInt, *, reason: str = MISSING) -> None:
        """Unpin a specific message in the channel.

        Similar to `pin_message()`; this requires the `MANAGE_MESSAGES`
        permission.

        Parameters:
            message: The message or ID to pin.
            reason: The audit log reason for pinning the message.
        """
        await get_api().unpin_message(self.id, message, reason=reason)


@attrs.define(eq=False)
class TextChannel(RawTextChannel):
    ...

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel.

        In general, this endpoint should **not** be used by bots. Only if
        something may take a few seconds should this be used to let the user
        know that it is being processed.
        """
        await get_api().trigger_typing(self.id)

    async def follow(self, target: SupportsInt) -> Snowflake:
        """Follow the channel.

        Returns:
            The ID of the webhook created.
        """
        data = await get_api().follow_channel(self.id, target)
        return Snowflake(data['webhook_id'])

    async def crosspost_message(self, message: SupportsInt) -> '_message.Message':
        """Crosspost a message in the current channel.

        Parameters:
            message: The message to crosspost to following channels.

        Returns:
            The same message which was crossposted.
        """
        data = await get_api().crosspost_message(self.id, message)
        return _message.Message.from_data(data)

    async def start_thread(
            self,
            *,
            name: str,
            message: SupportsInt = MISSING,
            archive_duration: Literal[60, 1440, 4320, 10080] = MISSING,
            slowmode_delay: int = MISSING,
            type: int = MISSING,
            invitable: bool = MISSING,
            reason: str = MISSING
    ) -> 'Thread':
        data = await get_api().start_thread(
            self.id, message, name=name, archive_duration=archive_duration,
            rate_limit=slowmode_delay, type=type, invitable=invitable,
            reason=reason,
        )
        return Thread.from_data(data)


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

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel.

        In general, this endpoint should **not** be used by bots. Only if
        something may take a few seconds should this be used to let the user
        know that it is being processed.
        """
        await get_api().trigger_typing(self.id)

    async def join(self) -> None:
        """Join the thread.

        The thread must not be archived or deleted to use this method.
        """
        await get_api().join_thread(self.id)

    async def leave(self) -> None:
        """Leave the joined thread.

        The thread must not be archived or deleted to use this method.
        """
        await get_api().leave_thread(self.id)


@attrs.define(eq=False)
class VoiceChannel(RawVoiceChannel):
    ...

    async def trigger_typing(self) -> None:
        """Trigger a typing indicator in the channel.

        In general, this endpoint should **not** be used by bots. Only if
        something may take a few seconds should this be used to let the user
        know that it is being processed.
        """
        await get_api().trigger_typing(self.id)


@attrs.define(eq=False)
class Category(RawCategory):
    ...
