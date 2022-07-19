from typing import (
    Any, Dict, Iterable, List, Optional, SupportsInt, Union, overload
)

from discord_typings import (
    AllowedMentionsData, ChannelData, ComponentData, EmbedData,
    FollowedChannelData, InviteData, ListThreadsData, MessageData,
    MessageReferenceData, PartialAttachmentData, PermissionOverwriteData,
    ThreadMemberData, UserData
)
from typing_extensions import Literal

from .._requester import Requester, RequestFiles
from .._route import Route
from .._utils import MISSING, dump_json

__all__ = (
    'ChannelEndpoints',
)


class ChannelEndpoints(Requester):
    """Channel-related endpoints under `/channels/`."""

    __slots__ = ()

    async def fetch_channel(self, channel: SupportsInt) -> ChannelData:
        """Fetch a channel by its ID.

        Parameters:
            channel: The ID of the channel to fetch.

        Returns:
            The channel object from Discord, including the `thread_member`
            object if the channel is a thread.
        """
        return await self.request(Route("GET", "/channels/{channel_id}", channel_id=int(channel)))

    # ChannelData has to be used for each of these overloads. For example,
    # even though a voice channel is edited, if only the position changes then
    # it'll match the text channel overload.

    @overload
    async def edit_channel(
        self,
        channel: SupportsInt,
        *,
        name: str = MISSING,
        position: Optional[int] = MISSING,
        nsfw: bool = MISSING,
        permission_overwrites: Optional[List[PermissionOverwriteData]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
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
        permission_overwrites: Optional[List[PermissionOverwriteData]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[Literal[1, 2]] = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
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
        permission_overwrites: Optional[List[PermissionOverwriteData]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
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
        permission_overwrites: Optional[List[PermissionOverwriteData]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
        ...

    @overload
    async def edit_channel(
            self,
            channel: SupportsInt,
            *,
            name: str = MISSING,
            archived: bool = MISSING,
            auto_archive: int = MISSING,
            locked: bool = MISSING,
            invitable: bool = MISSING,
            rate_limit: Optional[int] = MISSING,
            flags: int = MISSING,
            reason: str = MISSING,
    ) -> ChannelData:
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
        permission_overwrites: Optional[List[PermissionOverwriteData]] = MISSING,
        parent: Optional[SupportsInt] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[Literal[1, 2]] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        archived: bool = MISSING,
        auto_archive: int = MISSING,
        locked: bool = MISSING,
        invitable: bool = MISSING,
        flags: int = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
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
            archived: Whether the thread is archived.
            auto_archive: Duration in minutes for the thread to archive.
            locked: Whether the thread has been locked by a moderator.
            invitable:
                Whether non-moderators can add other non-moderators to the
                private thread (channel type 12).
            flags: Channel flags sent as a bitfield (can only set PINNED).
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
            'archived': archived,
            'auto_arcive_duration': auto_archive,
            'locked': locked,
            'invitable': invitable,
            'flags': flags,
        }

        return await self.request(
            Route('PATCH', '/channels/{channel_id}', channel_id=int(channel)),
            json=payload, reason=reason
        )

    async def delete_channel(
        self,
        channel: SupportsInt,
        *,
        reason: str = MISSING
    ) -> ChannelData:
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
        before: SupportsInt = MISSING,
        limit: int = 50
    ) -> List[MessageData]:
        ...

    @overload
    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        after: SupportsInt = MISSING,
        limit: int = 50
    ) -> List[MessageData]:
        ...

    @overload
    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        around: SupportsInt = MISSING,
        limit: int = 50
    ) -> List[MessageData]:
        ...

    async def fetch_messages(
        self,
        channel: SupportsInt,
        *,
        before: SupportsInt = MISSING,
        after: SupportsInt = MISSING,
        around: SupportsInt = MISSING,
        limit: int = 50
    ) -> List[MessageData]:
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
            'before': int(before) if before is not MISSING else MISSING,
            'after': int(after) if after is not MISSING else MISSING,
            'around': int(around) if around is not MISSING else MISSING
        }

        return await self.request(
            Route('GET', '/channels/{channel_id}/messages', channel_id=int(channel)),
            params=payload
        )

    async def fetch_message(self, channel: SupportsInt, message: SupportsInt) -> MessageData:
        """Fetch a specific message from a channel by its ID.

        On guild channels this requires the `READ_MESSAGE_HISTORY` permission.

        Parameters:
            channel: The ID of the channel to fetch the message from.
            message: The ID of the message to fetch.

        Returns:
            The message object if successful.
        """
        return await self.request(Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=int(channel), message_id=int(message)
        ))

    async def send_message(
        self,
        channel: SupportsInt,
        *,
        content: str = MISSING,
        tts: bool = MISSING,
        embeds: Iterable[EmbedData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        message_reference: MessageReferenceData = MISSING,
        components: List[ComponentData] = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Optional[PartialAttachmentData] = None,
        stickers: Iterable[SupportsInt] = MISSING
    ) -> MessageData:
        """Send a message into a channel.

        If the channel is a guild channel then the `SEND_MESSAGES` permission
        is required, replying to a message requires the `READ_MESSAGE_HISTORY`
        and to use `tts` required `SEND_TTS_MESSAGES` permission.

        Parameters:
            channel: The ID of the channel to send a message to.
            content: The content of the message.
            tts: Whether the message should be sent using text-to-speech.
            embeds: Embeds to send with the message.
            allowed_mentions: Rules for allowed mentions by the message.
            message_reference: Message reference information for replies.
            components: Message components to include with the message.
            files: Files to upload and attach with the message.
            stickers: Stickers to add to the message.

        Returns:
            The created message object.
        """

        if not any((content, embeds, files, stickers)):
            raise TypeError("one of 'content', 'embeds', 'file', 'stickers' is required")

        json = {
            'content': content,
            'tts': tts,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions,
            'message_reference': message_reference,
            'components': components,
            'attachments': attachments,
            'sticker_ids': [int(s) for s in stickers] if stickers else MISSING,
        }

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {'payload_json': dump_json(self._clean_dict(json))}

        # Files attached to Discord have to follow a special (odd) naming, so
        # we convert the simpler API of a list of open files to what can be
        # understood by both HTTPX and Discord.
        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'POST', '/channels/{channel_id}/messages',
                channel_id=int(channel)
            ),
            data=data, files=httpxfiles
        )

    async def crosspost_message(self, channel: SupportsInt, message: SupportsInt) -> MessageData:
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
            emoji: The emoji to react with.
        """
        await self.request(Route(
            'PUT', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=int(channel), message_id=int(message),
            emoji=str(emoji).strip('<>')
        ))

    async def delete_reaction(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        emoji: str,
        user: SupportsInt = MISSING
    ) -> None:
        """Delete a reaction on a message.

        If no user is specified the bot's reaction is removed. If a user is
        specified then the `MANAGE_MESSAGES` permission is required.

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
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}',
            channel_id=int(channel), message_id=int(message),
            emoji=str(emoji).strip('<>'), user_id=target
        ))

    async def fetch_reactions(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        emoji: str,
        *,
        after: SupportsInt = MISSING,
        limit: int = 25
    ) -> List[UserData]:
        """Fetch all users who have added the reaction to a specific message.

        This endpoint supports pagination with the `after` and `limit`
        parameters.

        Parameters:
            channel: The ID of the channel that the message is in.
            message: The ID of the message that the reactions are on.
            emoji: The emoji that is reacted with.
            after: The ID of the last user returned.
            limit:: The (1-100) amount of users to return.

        Returns:
            A list of users who have reacted with the emoji on the message.
        """
        return await self.request(
            Route(
                'GET', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
                channel_id=int(channel), message_id=int(message),
                emoji=str(emoji).strip('<>')
            ),
            params={'after': int(after) if after is not MISSING else after, 'limit': limit}
        )

    async def clear_reactions(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        emoji: str = MISSING
    ) -> None:
        """Delete all reactions on a message.

        This endpoint requires the `MANAGE_MESSAGES` permission.

        If an emojis is passed, only the reactions with that emojis are
        deleted, otherwise all reactions are removed.

        Parameters:
            channel: The ID of the channel the message is in.
            message: The ID of the message that has reactions:
            emoji: The specific emoji to remove all reactions of.
        """
        path = '/channels/{channel_id}/messages/{message_id}/reactions'
        params: Dict[str, Any] = {'channel_id': int(channel), 'message_id': int(message)}

        if emoji is not MISSING:
            path += '/{emoji}'
            params['emoji'] = str(emoji).strip('<>')

        await self.request(Route('DELETE', path, **params))

    async def edit_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Iterable[EmbedData]] = MISSING,
        flags: SupportsInt = MISSING,
        files: Optional[RequestFiles] = None,
        allowed_mentions: Optional[AllowedMentionsData] = MISSING,
        components: Optional[Iterable[ComponentData]] = MISSING,
        attachments: Optional[PartialAttachmentData] = MISSING
    ) -> MessageData:
        """Edit a previously sent message.

        If the bot is not the original author of the message only `flags` can
        be modified.

        If `content` is modified it is important to still pass
        `allowed_mentions` - otherwise it will be parsed with default values.

        Parameters:
            content: The content of the message.
            embeds: The embeds to edit the message to have.
            flags:
                The new flags of the message, the only value that can be
                changed is `SUPRESS_EMBEDS` (1 << 2).
            files:
                New files to upload. They must be given matching `attachments`
                objects to be added successfully.
            allowed_mentions: Allowed mentions to parse the new content with.
            attachments: Attachments to add, change or remove from the message.
            components: New message components to overwrite the old ones.

        Returns:
            The updated message object.
        """
        json: Dict[str, Any] = {
            'content': content,
            'embeds': embeds,
            'flags': int(flags) if flags is not MISSING else flags,
            'allowed_mentions': allowed_mentions,
            'components': components,
            'attachments': attachments
        }

        # This will cause HTTPX to use multipart/form-data
        data: Dict[str, Any] = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'PATCH', '/channels/{channel_id}/messages/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ),
            data=data, files=httpxfiles
        )

    async def delete_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a message by its ID.

        If the message was not sent by the bot this requires the
        `MANAGE_MESSAGES` permission.

        Parameters:
            channel: The ID of the channel the message is in.
            message: The ID of the message to delete.
            reason: The audit log reason for deleting the message.
        """
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

        This method can only be called with guild channels and requires the
        `MANAGE_MESSAGES` permission.

        All messages must not be older than 2 weeks, the list may not contain
        duplicates. Not following either of these guidelines will result in an
        exception.

        Parameters:
            channel: The ID of the channel the messages are in.
            messages: The IDs of the messages to delete.
            reason: The audit log reason for deleting the messages.
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
        type: Literal[0, 1],
        reason: str = MISSING
    ) -> None:
        """Edit channel permission overwrites for a user or role.

        This method can only be used on guild channels and requires the
        `MANAGE_ROLES` permission. Only permissions that the bot has in the
        guild or channel can be changed unless it has `MANAGE_ROLES`.

        Parameters:
            channel: The ID of the channel to edit the permission for.
            overwrite: The ID of the user or role to edit the permission for.
            allow: The new allowed permissions.
            deny: The new denied permissions.
            type:
                The type of the overwrite, either `0` for modifying permissions
                for a role or `1` for a user.
            reason: The audit log reason for changing the permission.
        """
        payload: Dict[str, Any] = {
            'allow': str(allow),
            'deny': str(deny),
            'type': type
        }
        await self.request(
            Route(
                'PUT', '/channels/{channel_id}/permissions/{overwrite_id}',
                channel_id=int(channel), overwrite_id=int(overwrite)
            ),
            json=payload, reason=reason
        )

    async def fetch_channel_invites(self, channel: SupportsInt) -> List[InviteData]:
        """Fetch all invites created on a channel.

        This method requires the `MANAGE_CHANNELS` permission.

        Parameters:
            channel: The ID of the channel to fetch invites from.

        Returns:
            A list of invite objects.
        """
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
    ) -> InviteData:
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
        target_type: Literal[1, 2],
        target: SupportsInt,
        reason: str = MISSING
    ) -> InviteData:
        ...

    async def create_invite(
        self,
        channel: SupportsInt,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: Literal[1, 2] = MISSING,
        target: SupportsInt = MISSING,
        reason: str = MISSING
    ) -> InviteData:
        """Create a new channel invite.

        This method can only be used on guild channels and requires the
        `CREATE_INSTANT_INVITE` permission.

        Parameters:
            channel: The ID of the channel to create the invite in.
            max_age:
                How long the invite should last in seconds, use 0 for a never
                expiring invite.
            max_uses: How many times the invite can be used, 0 means unlimited.
            temporary: Whether the invite only grants temporary membership.
            unique:
                Whether the returned invite must be new. Discord re-uses
                similar invites sometimes, so the returned invite may not be
                new.
            target_type:
                The type of the invite target, use `1` for a stream and `2`
                for an embedded application.
            target:
                Depending on the target type this is either the ID of the user
                who is streaming for target type `1`, otherwise the ID of the
                application that is embedded.
            reason: The audit log reason for creating the invite.

        Returns:
            The created invite object.
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
        """Delete a channel permission overwrite.

        This method can only be used on guild channels and requires the
        `MANAGE_ROLES` permission.

        Parameters:
            channel: The ID of the channel to delete the permission from.
            overwrite: The ID of the user or role to delete the permission for.
            reason: The audit log reason for deleting the permission.
        """
        await self.request(
            Route(
                'PUT', '/channels/{channel_id}/permissions/{overwrite_id}',
                channel_id=int(channel), overwrite_id=int(overwrite)
            ),
            reason=reason
        )

    async def follow_channel(
        self,
        channel: SupportsInt,
        target: SupportsInt
    ) -> FollowedChannelData:
        """Follow a news channel to send messages to a target channel.

        This can only be used on guild channels and requires the
        `MANAGE_WEBHOOKS` permission to perform.

        Parameters:
            channel: The ID of the channel to follow.
            target: The ID of the target channel to send messages to.

        Returns:
            A "followed channel" response which contains the created webhook
            (`webhook_id`) and the source channel (`channel_id`).
        """
        return await self.request(
            Route('POST', '/channels/{channel_id}/followers', channel_id=int(channel)),
            json={'webhook_channel_id': int(target)}
        )

    async def trigger_typing(self, channel: SupportsInt) -> None:
        """Trigger a typing indicator in a channel.

        In general, this endpoint should **not** be used by bots. Only if
        something may take a few seconds should this be used to let the user
        know that it is being processed.
        """
        await self.request(Route(
            'POST', '/channels/{channel_id}/typing', channel_id=int(channel)
        ))

    async def fetch_pins(self, channel: SupportsInt) -> List[MessageData]:
        """Fetch all pinned messages in a channel.

        Parameters:
            channel: The ID of the channel to fetch pins from.

        Returns:
            A list of message objects that are pinned.
        """
        return await self.request(Route(
            'GET', '/channels/{channel_id}/pins', channel_id=int(channel)
        ))

    async def pin_message(
        self,
        channel: SupportsInt,
        message: SupportsInt,
        *,
        reason: str = MISSING
    ) -> None:
        """Pin a message in a channel.

        This method requires the `MANAGE_MESSAGES` permission. The maximum
        amount of pinned messages is 50.

        Parameters:
            channel: The ID of the channel to pin the message in.
            message: The ID of the message to pin.
            reason: The audit log reason for pinning the message.
        """
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
    ) -> None:
        """Unpin a message from a channel.

        Similar to `pin_message()` this requires the `MANAGE_MESSAGES`
        permission to execute.

        Parameters:
            channel: The ID of the channel to unpin the message from.
            message: The ID of the message to unpin.
            reason: The audit log reason for unpinning the message.
        """
        await self.request(
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
        archive_duration: Literal[60, 1440, 4320, 10080] = MISSING,
        rate_limit: int = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
        ...

    @overload
    async def start_thread(
        self,
        channel: SupportsInt,
        *,
        name: str,
        archive_duration: Literal[60, 1440, 4320, 10080] = MISSING,
        rate_limit: int = MISSING,
        type: int,
        invitable: bool = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
        ...

    async def start_thread(
        self,
        channel: SupportsInt,
        message: SupportsInt = MISSING,
        *,
        name: str,
        archive_duration: Literal[60, 1440, 4320, 10080] = MISSING,
        rate_limit: int = MISSING,
        type: int = MISSING,
        invitable: bool = MISSING,
        reason: str = MISSING
    ) -> ChannelData:
        """Start a new thread in a channel.

        Depending on whether `message` is passed the thread will be started
        with or without a message (these are two different endpoints).

        If no `message` is passed, the thread defaults to a private thread.
        If a `message` is passed, the type of thread depends on the type of
        channel that was passed. The ID of the thread is the same as the ID of
        the message it was created on.

        Parameters:
            channel: The ID of the channel to start the thread in.
            message: The optional ID of the message to start the thread on.
            name: The 1-100 character name of the thread.
            archive_duration:
                After how many minutes after recent activity the thread should
                be archived automatically.
            rate_limit:
                Amount of seconds (0-21600) users need to wait before
                sending another message.
            type: The type of thread to create. Pass in a channel type.
            invitable:
                Whether non-moderators can add non-moderators to the thread.
                This can only be passed if you are creating a private thread.
            reason: The audit log reason for starting the thread.

        Returns:
            The created thread object.
        """
        if message is not MISSING and type is MISSING:
            raise TypeError('thread type is required when starting a thread without a message')

        path = '/channels/{channel_id}'
        params: Dict[str, Any] = {'channel_id': int(channel)}

        payload: Dict[str, Any] = {
            'name': name,
            'auto_archive_duration': archive_duration,
            'rate_limit_per_user': rate_limit,
        }

        if message is not MISSING:
            path += '/messages/{message_id}'
            params['message_id'] = int(message)

            payload['type'] = type
            if invitable is not MISSING:
                payload['invitable'] = invitable

        return await self.request(
            Route('POST', f'{path}/threads', **params), json=payload, reason=reason
        )

    async def join_thread(self, channel: SupportsInt) -> None:
        """Make the bot user join a thread.

        The thread must not be archived or deleted to use this method.

        Parameters:
            channel: The ID of the thread to join.
        """
        await self.request(
            Route('PUT', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel))
        )

    async def add_thread_member(self, channel: SupportsInt, user: SupportsInt) -> None:
        """Add another member to a thread.

        This method requires the ability to send messages in the thread and
        that it is not archived or deleted. Trying to add a member that already
        is in the thread does not fail.

        Parameters:
            channel: The ID of the thread to add the member to.
            user: The ID of the member to add to the thread.
        """
        await self.request(Route(
            'PUT', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def leave_thread(self, channel: SupportsInt) -> None:
        """Make the bot user leave a thread.

        The thread can't be archived for this to succeed.

        Parameters:
            channel: The ID of the thread to leave.
        """
        await self.request(Route(
            'DELETE', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel)
        ))

    async def remove_thread_member(self, channel: SupportsInt, user: SupportsInt) -> None:
        """Remove another member from a thread.

        This method requires the `MANAGE_THREADS` permission or that the bot is
        the creator of the thread if it is a `GUILD_PRIVATE_THREAD`. The thread
        can't be archived.

        Parameters:
            channel: The ID of the thread to remove the member from.
            user: The ID of the member to remove from the thread.
        """
        await self.request(Route(
            'DELETE', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def fetch_thread_member(self, channel: SupportsInt, user: SupportsInt) -> ThreadMemberData:
        """Fetch thread member information about a member in a thread.

        If the member has not yet joined the thread a 404 NotFound error will
        be raised.

        Parameters:
            channel: The ID of the thread the member is in.
            user: The ID of the member to fetch information about.

        Returns:
            The thread member information for the member.
        """
        return await self.request(Route(
            'GET', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def fetch_thread_members(self, channel: SupportsInt) -> List[ThreadMemberData]:
        """Fetch all members who have joined a particular thread.

        This method requires the `GUILD_MEMBERS` priviledged intent.

        Parameters:
            channel: The ID of the thread to fetch members from.

        Returns:
            A list of thread member data.
        """
        return await self.request(
            Route('GET', '/channels/{channel_id}/thread-members', channel_id=int(channel))
        )

    async def fetch_public_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: str = MISSING,
        limit: int = MISSING,
    ) -> ListThreadsData:
        """Fetch all archived public threads.

        The returned threads are ordered by their `archive_timestamp` in
        descending order. This method requires the `READ_MESSAGE_HISTORY`
        permission to execute.

        Parameters:
            channel: The ID of the channel to fetch threads from.
            before: The timestamp to fetch threads that were archived before.
            limit: The maximum number of threads to return.

        Return:
            A special object with a `threads`, `members`, and `has_more` keys.
        """
        query = {
            'before': before,
            'limit': limit
        }

        return await self.request(
            Route(
                'GET', '/channels/{channel_id}/threads/archived/public',
                channel_id=int(channel)
            ),
            params=query
        )

    async def fetch_private_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: str = MISSING,
        limit: int = MISSING
    ) -> ListThreadsData:
        """Fetch all archived private threads.

        Similar to `fetch_public_archived_threads` the threads are ordered by
        their `archive_timestamp` in descending order. This method requires
        *both* the `READ_MESSAGE_HISTORY` and `MANAGE_THREADS` permission.

        Parameters:
            channel: The ID of the channel to fetch threads from.
            before: The timestamp to fetch threads that were archived before.
            limit: The maximum number of threads to return.

        Returns:
            A special object with a `threads`, `members`, and `has_more` keys.
        """
        query = {
            'before': before,
            'limit': limit,
        }

        return await self.request(
            Route(
                'GET', '/channels/{channel_id}/threads/archived/public',
                channel_id=int(channel)
            ),
            params=query
        )

    async def fetch_joined_private_archived_threads(
        self,
        channel: SupportsInt,
        *,
        before: int = MISSING,
        limit: int = MISSING
    ) -> ListThreadsData:
        """Fetch all joined archived private threads.

        The threads are ordered by their ID. Compared to
        `fetch_private_archived_threads()` this endpoint only requires the
        `READ_MESSAGE_HISTORY` permission.`

        Parameters:
            channel: The ID of the channel to fetch threads from.
            before: The ID of the thread to fetch threads before.
            limit: The maximum number of threads to return.

        Returns:
            A special object with a `threads`, `members`, and `has_more` keys.
        """
        query = {
            'before': before,
            'limit': limit,
        }

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )
