from typing import (
    Any, Dict, List, Literal, Optional, Sequence, SupportsInt, Union, overload
)
from urllib.parse import quote as urlquote

from ..ratelimiter import Route
from ..utils import MISSING, File
from .base import Requester


class ChannelRequester(Requester):
    """Channel related endpoints."""

    async def fetch_channel(self, channel: SupportsInt):
        """Fetch a channel by its ID.

        Parameters:
            channel: The ID of the channel to fetch.

        Returns:
            The channel object from Discord, including the `thread_member`
            object if the channel is a thread.
        """
        return await self.request(Route("GET", "/channels/{channel_id}", channel_id=int(channel)))

    @overload
    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        position: Optional[int] = MISSING,
        nsfw: bool = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        position: int = MISSING,
        bitrate: Optional[int] = MISSING,
        user_limit: Optional[int] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        type: int = MISSING,
        position: Optional[int] = MISSING,
        topic: Optional[str] = MISSING,
        nsfw: Optional[bool] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        type: int = MISSING,
        position: Optional[int] = MISSING,
        topic: Optional[str] = MISSING,
        nsfw: Optional[bool] = MISSING,
        rate_limit: Optional[int] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        type: int = MISSING,
        position: Optional[int] = MISSING,
        topic: Optional[str] = MISSING,
        nsfw: Optional[bool] = MISSING,
        rate_limit: Optional[int] = MISSING,
        bitrate: Optional[int] = MISSING,
        user_limit: Optional[int] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[Literal[1, 2]] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit the settings of a channel.

        The `MANAGE_CHANNELS` permission is required to edit the channel. Only
        permissions your bot has in the guild or channel can be changed and
        doing so requires the `MANAGE_ROLES` permission.

        Parameters:
            channel: The ID of the channel to edit.
            name: The new 1-100 character name.
            type:
                The new type of channel; can only change between text- and news
                channels in guilds with the `"GUILDS"` feature.
            position: The new position of the channel.
            topic: The new 0-1024 character topic of the channel.
            nsfw: Whether the channel is NSFW or not.
            rate_limit:
                The new rate at which the user is allowed to interact with the
                channel. This is commonly known as slowmode.
            bitrate:
                The new bitrate (in bits) of the channel. Allowed values are
                8'000 to 96'000 or 128'000 for VIP servers.
            user_limit:
                The maximum amount of users in the voice channel. 0 refers to
                no limit, while any value between 1 and 99 indicates a limit.
            permission_overwrites:
                List of permission overwrites to apply to this channel. Passing
                this option requires the `MANAGE_ROLES` permission.
            parent:
                The new ID of the parent category. Can be set to None to move
                the channel outside of any category.
            rtc_region: Channel voice region; None makes it automatic.
            video_quality: Video quality mode. 0 is automatic and 1 is full.
            default_auto_archive:
                The default value for the automatic archival of threads created
                in this channel.
            reason: The reason shown in the audit log for editing this channel.

        Returns:
            The new channel object after the changes had been applied.
        """
        # The amount of complexity necessary to ensure the user has passed a
        # good combination of options is too much for the library to bother at
        # this moment. The typing overloads should be enough.

        # Requester.request() will clean up the MISSING pairs
        payload: Dict[str, Any] = {
            'name': name,
            'type': type,
            'position': position,
            'topic': topic,
            'nsfw': nsfw,
            'rate_limit_per_user': rate_limit,
            'bitrate': bitrate,
            'user_limit': user_limit,
            'permission_overwrites': permission_overwrites,
            'parent_id': parent,
            'rtc_region': rtc_region,
            'video_quality_mode': video_quality,
            'default_auto_archive_duration': default_auto_archive,
        }

        return await self.request(
            Route('PATCH', '/channels/{channel_id}', channel_id=int(channel)),
            json=payload, reason=reason
        )

    async def delete_channel(self, channel: SupportsInt, *, reason: str = MISSING) -> Dict[str, Any]:
        """Delete a channel, or close a private message.

        Requires the `MANAGE_CHANNELS` or `MANAGE_THREADS` permission. Deleting
        a category still keeps all the channels.

        Parameters:
            channel: The ID of the channel to delete.
            reason: The reason shown in the Audit log for deleting the channel.

        Returns:
            The full channel object is returned on success.
        """
        return await self.request(
            Route('DELETE', '/channels/{channel_id}', channel_id=int(channel)),
            reason=reason
        )

    @overload
    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        after: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        around: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        after: int = MISSING,
        around: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        """Fetch messages in a channel.

        The `VIEW_CHANNEL` permossion is required, if the bot is missing the
        `READ_MESSAGE_HISTORY` permission this returns nothing.

        The Snowflake passed to `before`, `after` or `around` does not need to
        be a valid message ID. All Discord does is read the timestamp.

        Parameters:
            channel: The ID of the channel to fetch messages from.
            before: Snowflake to fetch messages before.
            after: Snowflake to fetch messages after.
            around: Snowflake to fetch messages around.
            limit: The amount of messages to fetch.

        Returns:
            The list of messages fetched that meets the criteria.
        """
        if bool(before) + bool(after) + bool(around) > 1:
            raise TypeError("'before', 'after' and 'around' are mutually exclusive")
        elif 0 > limit > 100:
            raise TypeError("'limit' must be a number between 1 and 100")

        payload: Dict[str, Any] = {
            'limit': limit,
            'before': before,
            'after': after,
            'around': around
        }

        return await self.request(
            Route('GET', '/channels/{channel_id}/messages', channel_id=int(channel)),
            params=payload
        )

    async def fetch_message(self, channel: SupportsInt, message: SupportsInt) -> Dict[str, Any]:
        """Fetch a specific message from a channel by its ID."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=int(channel), message_id=int(message)
        ))

    async def send_message(
        self,
        channel: SupportsInt,
        *,
        content: str = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
        stickers: Sequence[SupportsInt] = MISSING
    ) -> Dict[str, Any]:
        """Send a message into a channel."""

        if not any((content, embeds, file, stickers)):
            raise TypeError("one of 'content', 'embeds', 'file', 'stickers' is required")

        json: Dict[str, Any] = {
            'content': content,
            'username': username,
            'avatar_url': str(avatar_url) if avatar_url else MISSING,
            'tts': tts,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else MISSING,
            'sticker_ids': [int(s) for s in stickers] if stickers else MISSING,
        }
        json = self._clean_dict(json)

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file is not MISSING:
            data['file'] = file

        return await self.request(
            Route(
                'POST', '/channels/{channel_id}/messages',
                channel_id=int(channel)
            ),
            data=data
        )

    async def crosspost_message(self, channel: SupportsInt, message: SupportsInt) -> Dict[str, Any]:
        """Crosspost a message in a news channel to following channels.

        This requires the `SEND_MESSAGES` permission if the bot is the author
        of the message, otherwise it also requires `MANAGE_MESSAGES`.

        Parameters:
            channel: The ID of the news channel the message was posted in.
            message: The ID of the message to crosspost.

        Returns:
            The full crossposted message object.
        """
        return await self.request(Route(
            'POST', '/channels/{channel_id}/messages/{message_id}/crosspost',
            channel_id=int(channel), message_id=int(message)
        ))

    async def add_reaction(self, channel: SupportsInt, message: SupportsInt, emoji: str) -> None:
        """Add a reaction to a message.

        This endpoint requires the `READ_MESSAGE_HISTORY`, and `ADD_REACTIONS`
        if no other user has already reacted with this emoji on that message.

        Parameters:
            channel: The ID of the channel.
            message: The ID of the message.
            emoji:
                The emoji to react with, if this is a custom emoji it must be
                in the format `name:id` without the greater than/less than
                symbols normally required.
        """
        await self.request(Route(
            'PUT', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=int(channel), message_id=int(message), emoji=urlquote(str(emoji))
        ))

    async def delete_reaction(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        emoji: str,
        user: SupportsInt = MISSING
    ) -> None:
        """Delete a reaction on a message.

        If no user is specified the bot's reaction is removed.

        Parameters:
            channel: The ID of the channel.
            message: The ID of the message.
            emoji: The specific emoji reacted on the messsage to remove.
            user:
                The user who's reaction to remove. If not user is specified the
                bot's own reaction will be removed.
        """
        # We int() user here so that we don't need to figure it out below
        target: Union[str, int] = '@me' if user is MISSING else int(user)

        return await self.request(Route(
            'DELETE', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}',
            channel_id=int(channel), message_id=int(message),
            emoji=urlquote(str(emoji)), user_id=target
        ))

    async def fetch_reactions(self, channel: SupportsInt, message: SupportsInt, emoji: str) -> List[Any]:
        """Fetch all users who have added the reaction to a specific message."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=int(channel), message_id=int(message), emoji=urlquote(str(emoji))
        ))

    async def clear_reactions(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        emoji: str = MISSING
    ) -> None:
        """Delete all reactions on a message.

        If an emojis is passed, only the reactions with that emojis are deleted.
        """
        path = '/channels/{channel_id}/messages/{message_id}/reactions'
        params: Dict[str, Any] = {'channel_id': int(channel), 'message_id': int(message)}

        if emoji is not MISSING:
            path += '/{emoji}'
            params['emoji'] = str(emoji)

        await self.request(Route('DELETE', path, **params))

    async def edit_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        file: Optional[File] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        attachments: Optional[Dict[str, Any]] = MISSING
    ) -> Dict[str, Any]:
        """Edit a previously sent message."""
        json: Dict[str, Any] = {
            'content': content,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else allowed_mentions,
            'attachments': attachments
        }
        json = self._clean_dict(json)

        # This will cause HTTPx to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file is not MISSING:
            data['file'] = file

        return await self.request(
            Route(
                'PATCH', '/channels/{channel_id}/messages/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ),
            data=data
        )

    async def delete_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a message by its ID."""
        return await self.request(
            Route(
                'DELETE', '/channels/{channel_id}/messages/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ), reason=reason
        )

    async def bulk_delete_messages(
        self,
        channel: SupportsInt,
        messages: List[SupportsInt],
        *,
        reason: str = MISSING
    ) -> None:
        """Delete multiple messages in a single request.

        All messages must not be older than 2 weeks, the list may not contain
        duplicates. Not following either of these guidelines will result in an exception.
        """
        await self.request(
            Route(
                'POST', '/channels/{channel_id}/messages/bulk-delete',
                channel_id=int(channel)
            ), json={'messages': [int(m) for m in messages]}, reason=reason
        )

    async def set_permission(
        self,
        channel: SupportsInt,
        overwrite: SupportsInt,
        *,
        allow: Union[str, int],
        deny: Union[str, int],
        type: PermissionTarget,
        reason: str = MISSING
    ) -> None:
        """Edit channel permission overwrites for a user or role."""
        payload: Dict[str, Any] = {
            'allow': str(allow),
            'deny': str(deny),
            'type': type.value
        }
        await self.request(
            Route(
                'PUT', '/channels/{channel_id}/permissions/{overwrite_id}',
                channel_id=int(channel), overwrite_id=int(overwrite)
            ),
            json=payload, reason=reason
        )

    async def fetch_channel_invites(self, channel: SupportsInt) -> List[Any]:
        """Fetch all invites created on a channel."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/invites',
            channel_id=int(channel)
        ))

    @overload
    async def create_invite(
        self,
        channel: SupportsInt,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def create_invite(
        self,
        channel: SupportsInt,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: int,
        target: SupportsInt,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    async def create_invite(
        self,
        channel: SupportsInt,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: int = MISSING,
        target: SupportsInt = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new channel invite.

        `target` wraps both `target_user_id` and `target_application_id` depending
        on what `target_type` is set.
        """
        if target_type is not MISSING and target is MISSING:
            raise TypeError("'target' is required when 'target_type' is passed")

        payload: Dict[str, Any] = {
            'max_age': max_age,
            'max_uses': max_uses,
            'temporary': temporary,
            'unique': unique
        }

        if target_type == 1:
            payload['target_type'] = target_type
            payload['target_user_id'] = target

        elif target_type == 2:
            payload['target_type'] = target_type
            payload['target_application_id'] = target

        return await self.request(
            Route(
                'POST', '/channels/{channel_id}/invites',
                channel_id=int(channel)
            ), reason=reason, json=payload
        )

    async def delete_permission(
        self,
        channel: SupportsInt,
        overwrite: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a channel permission overwrite."""
        await self.request(
            Route(
                'PUT', '/channels/{channel_id}/permissions/{overwrite_id}',
                channel_id=int(channel), overwrite_id=int(overwrite)
            ),
            reason=reason
        )

    async def follow_channel(self, channel: SupportsInt, target: SupportsInt) -> Dict[str, Any]:
        """Follow a news channel to send messages to a target channel."""
        return await self.request(
            Route('POST', '/channels/{channel_id}/followers', channel_id=int(channel)),
            json={'webhook_channel_id': int(target)}
        )

    async def trigger_typing(self, channel: SupportsInt) -> None:
        """Trigger a typing indicator in a channel."""
        await self.request(Route('POST', '/channels/{channel_id}/typing', channel_id=int(channel)))

    async def fetch_pins(self, channel: SupportsInt) -> List[Any]:
        """Fetch all pinned messages in a channel."""
        return await self.request(Route('GET', '/channels/{channel_id}/pins', channel_id=int(channel)))

    async def pin_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Pin a message in a channel."""
        return await self.request(
            Route(
                'PUT', '/channels/{channel_id}/pins/{message_id}',
                channel=int(channel), message_id=int(message)
            ), reason=reason
        )

    async def unpin_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Unpin a message in a channel."""
        return await self.request(
            Route(
                'DELETE', '/channels/{channel_id}/pins/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ),
            reason=reason
        )

    @overload
    async def start_thread(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        name: str,
        archive_duration: Literal[60, 1440, 4320, 10080],
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def start_thread(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        name: str,
        archive_duration: Literal[60, 1440, 4320, 10080],
        type: int,
        invitable: bool = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    async def start_thread(
        self,
        channel: SupportsInt,
        message: SupportsInt = MISSING,
        *,
        name: str,
        archive_duration: int,
        type: int = MISSING,
        invitable: bool = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new thread in a channel, with or without an existing message."""
        if message is not MISSING and type is MISSING:
            raise TypeError('thread type is required when starting a thread without a message')

        path = '/channels/{channel_id}'
        params: Dict[str, Any] = {'channel_id': int(channel)}

        payload: Dict[str, Any] = {
            'name': name,
            'auto_archive_duration': archive_duration
        }

        if message is not MISSING:
            path += '/messages/{message_id}'
            params['message_id'] = int(message)

            payload['type'] = type
            if invitable is not MISSING:
                payload['invitable'] = invitable

        return await self.request(
            Route('POST', path + '/threads', **params),
            json=payload, reason=reason
        )

    async def join_thread(self, channel: SupportsInt) -> None:
        """Make the bot user join a thread."""
        await self.request(
            Route('PUT', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel))
        )

    async def add_thread_member(self, channel: SupportsInt, user: SupportsInt) -> None:
        """Add another member to a thread."""
        await self.request(Route(
            'PUT', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def leave_thread(self, channel: SupportsInt) -> None:
        """Make the bot user leave a thread."""
        await self.request(
            Route('DELETE', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel))
        )

    async def remove_thread_member(self, channel: SupportsInt, user: SupportsInt) -> None:
        """Remove another member to a thread."""
        await self.request(Route(
            'DELETE', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def fetch_thread_members(self, channel: SupportsInt) -> List[Any]:
        """Fetch all members who have joined a thread."""
        return await self.request(
            Route('GET', '/channels/{channel_id}/thread-members', channel_id=int(channel))
        )

    async def fetch_public_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        limit: int = MISSING,
    ) -> Dict[str, Any]:
        """Fetch all archived public threads."""
        query: Dict[str, Any] = {
            'before': before,
            'limit': limit
        }
        query = self._clean_dict(query)

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )

    async def fetch_private_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        limit: int = MISSING
    ) -> Dict[str, Any]:
        """Fetch all archived private threads."""
        query: Dict[str, Any] = {
            'before': before,
            'limit': limit,
        }
        query = self._clean_dict(query)

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )

    async def fetch_joined_private_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        limit: int = MISSING
    ) -> Dict[str, Any]:
        """Fetch all joined archived private threads."""
        query: Dict[str, Any] = {
            'before': before,
            'limit': limit,
        }
        query = self._clean_dict(query)

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )
