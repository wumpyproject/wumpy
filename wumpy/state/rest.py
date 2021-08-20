from typing import (
    TYPE_CHECKING, Any, Dict, List, Literal, Optional, Sequence, Union,
    overload
)
from urllib.parse import quote as urlquote

from ..models import AllowedMentions, PermissionOverwrite
from ..rest import File, Route, WebhookRequester
from ..utils import MISSING

if TYPE_CHECKING:
    from .state import ApplicationState


__all__ = ('RESTClient',)


class RESTClient(WebhookRequester):
    """Requester subclass wrapping endpoints used for Discord applications."""

    _state: 'ApplicationState'

    __slots__ = ('_state',)

    def __init__(self, state: 'ApplicationState', token: str, *args, **kwargs):
        super().__init__(*args, **kwargs, headers={"Authorization": f"Bot {token}"})

        self._state = state

    # Audit Log endpoints

    async def fetch_audit_logs(self, guild: int) -> Dict[str, Any]:
        """Fetch the audit log entries for this guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=guild))

    # Asset endpoint

    async def read_asset(self, url: str, *, size: int) -> bytes:
        return await self._bypass_request('GET', url, size=size)

    # Channel endpoints

    async def fetch_channel(self, channel: int):
        """Fetch a channel by its ID."""
        return await self.request(Route("GET", "/channels/{channel_id}", channel_id=int(channel)))

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: str = MISSING,
        position: Optional[int] = MISSING,
        nsfw: bool = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a Store channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: str = MISSING,
        position: int = MISSING,
        bitrate: Optional[int] = MISSING,
        user_limit: Optional[int] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[int] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a Voice channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: str = MISSING,
        type: int = MISSING,
        position: Optional[int] = MISSING,
        topic: Optional[str] = MISSING,
        nsfw: Optional[bool] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[int] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a News channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: str = MISSING,
        type: int = MISSING,
        position: Optional[int] = MISSING,
        topic: Optional[str] = MISSING,
        nsfw: Optional[bool] = MISSING,
        rate_limit: Optional[int] = MISSING,
        permission_overwrites: Optional[List[PermissionOverwrite]] = MISSING,
        parent: Optional[int] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a Text channel by its ID."""
        ...

    async def edit_channel(
        self,
        channel: int,
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
        parent: Optional[int] = MISSING,
        rtc_region: Optional[str] = MISSING,
        video_quality: Optional[int] = MISSING,
        default_auto_archive: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        # The amount of complexity necessary to ensure the user has passed a good
        # combination of options is too much for the library to bother at this moment

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

    async def delete_channel(self, channel: int, *, reason: str = MISSING):
        """Delete a channel by its ID."""
        return await self.request(
            Route('DELETE', '/channels/{channel_id}', channel_id=int(channel)),
            reason=reason
        )

    @overload
    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        before: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        after: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        around: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        ...

    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        before: int = MISSING,
        after: int = MISSING,
        around: int = MISSING,
        limit: int = 50
    ) -> List[Any]:
        """Fetch the messages for a channel by its ID."""
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

    async def fetch_channel_message(self, channel: int, message: int) -> Dict[str, Any]:
        """Fetch a specific message from a channel by its ID."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=int(channel), message_id=int(message)
        ))

    async def send_message(
        self,
        channel: int,
        *,
        wait: bool = False,
        thread: int = MISSING,
        content: str = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
        stickers: Sequence[int] = MISSING
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

    async def crosspost_message(self, channel: int, message: int) -> Dict[str, Any]:
        """Crosspost a message in a news channel to following channels."""
        return await self.request(Route(
            'POST', '/channels/{channel_id}/messages/{message_id}/crosspost',
            channel_id=int(channel), message_id=int(message)
        ))

    async def add_reaction(self, channel: int, message: int, emoji: str) -> None:
        """Add a reaction to a message."""
        await self.request(Route(
            'PUT', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=int(channel), message_id=int(message), emoji=urlquote(str(emoji))
        ))

    async def delete_reaction(
        self,
        channel: int,
        message: int,
        emoji: str,
        user: int = MISSING
    ) -> None:
        """Delete a reaction, if no user is passed then the bot's own reaction is deleted."""
        # We int() user here so that we don't need to figure it out below
        target: Union[str, int] = '@me' if user is MISSING else int(user)

        return await self.request(Route(
            'DELETE', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}',
            channel_id=int(channel), message_id=int(message),
            emoji=urlquote(str(emoji)), user_id=target
        ))

    async def fetch_reactions(self, channel: int, message: int, emoji: str) -> List[Any]:
        """Fetch all users who have added the reaction to a specific message."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=int(channel), message_id=int(message), emoji=urlquote(str(emoji))
        ))

    async def clear_reactions(self, channel: int, message: int, emoji: str = MISSING) -> None:
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
        channel: int,
        message: int,
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

        # This will cause aiohttp to use multipart/form-data
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

    async def delete_message(self, channel: int, message: int, *, reason: str = MISSING) -> None:
        """Delete a message by its ID."""
        return await self.request(
            Route(
                'DELETE', '/channels/{channel_id}/messages/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ), reason=reason
        )

    async def bulk_delete_messages(
        self,
        channel: int,
        messages: List[int],
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
            ), json={'messages': messages}, reason=reason
        )

    async def set_channel_permission(
        self,
        channel: int,
        overwrite: int,
        *,
        allow: Union[str, int],
        deny: Union[str, int],
        type: Literal[0, 1],
        reason: str = MISSING
    ) -> None:
        """Edit channel permission overwrites for a user or role."""
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

    async def fetch_channel_invites(self, channel: int) -> List[Any]:
        """Fetch all invites created on a channel."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/invites',
            channel_id=int(channel)
        ))

    @overload
    async def create_invite(
        self,
        channel: int,
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
        channel: int,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: int,
        target: int,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    async def create_invite(
        self,
        channel: int,
        *,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = False,
        target_type: int = MISSING,
        target: int = MISSING,
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

    async def delete_channel_permission(
        self,
        channel: int,
        overwrite: int,
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

    async def follow_news_channel(self, channel: int, target: int) -> Dict[str, Any]:
        """Follow a news channel to send messages to a target channel."""
        return await self.request(
            Route('POST', '/channels/{channel_id}/followers', channel_id=int(channel)),
            json={'webhook_channel_id': int(target)}
        )

    async def trigger_typing(self, channel: int) -> None:
        """Trigger a typing indicator in a channel."""
        await self.request(Route('POST', '/channels/{channel_id}/typing', channel_id=int(channel)))

    async def fetch_pins(self, channel: int) -> List[Any]:
        """Fetch all pinned messages in a channel."""
        return await self.request(Route('GET', '/channels/{channel_id}/pins', channel_id=int(channel)))

    async def pin_message(self, channel: int, message: int, *, reason: str = MISSING) -> None:
        """Pin a message in a channel."""
        return await self.request(
            Route(
                'PUT', '/channels/{channel_id}/pins/{message_id}',
                channel=int(channel), message_id=int(message)
            ), reason=reason
        )

    async def unpin_message(
        self,
        channel: int,
        message: int,
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
        channel: int,
        message: int,
        *,
        name: str,
        archive_duration: Literal[60, 1440, 4320, 10080],
        reason: str = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def start_thread(
        self,
        channel: int,
        message: int,
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
        channel: int,
        message: int = MISSING,
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

    async def join_thread(self, channel: int) -> None:
        """Make the bot user join a thread."""
        await self.request(
            Route('PUT', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel))
        )

    async def add_thread_member(self, channel: int, user: int) -> None:
        """Add another member to a thread."""
        await self.request(Route(
            'PUT', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def leave_thread(self, channel: int) -> None:
        """Make the bot user leave a thread."""
        await self.request(
            Route('DELETE', '/channels/{channel_id}/thread-members/@me', channel_id=int(channel))
        )

    async def remove_thread_member(self, channel: int, user: int) -> None:
        """Remove another member to a thread."""
        await self.request(Route(
            'DELETE', '/channels/{channel_id}/thread-members/{user_id}',
            channel_id=int(channel), user_id=int(user)
        ))

    async def fetch_thread_members(self, channel: int) -> List[Any]:
        """Fetch all members who have joined a thread."""
        return await self.request(
            Route('GET', '/channels/{channel_id}/thread-members', channel_id=int(channel))
        )

    async def fetch_public_archived_threads(
        self,
        channel: int,
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
        channel: int,
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
        channel: int,
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

    # Emoji endpoints

    async def fetch_emojis(self, guild: int) -> List[Any]:
        """Fetch all emojis in a guild by its ID."""
        return await self.request(Route('GET', '/guilds/{guild_id}', guild_id=guild))

    async def fetch_emoji(self, guild: int, emoji: int) -> Dict[str, Any]:
        """Fetch a specific emoji from a guild by its ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/emojis/{emoji_id}',
            guild_id=int(guild), emoji_id=int(emoji)
        ))

    async def create_emoji(
        self,
        guild: int,
        *,
        name: str,
        image: str,
        roles: Optional[Sequence[int]] = None,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create an emoji in a guild."""
        payload = {
            'name': name,
            'image': image,
            # We can't iterate through None, so we need to add an additional
            # gate so that we simply pass None if it is
            'roles': [int(r) for r in roles] if roles else None
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/emojis', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_emoji(
        self,
        guild: int,
        emoji: int,
        *,
        name: str = MISSING,
        roles: List[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit fields of an emoji by its ID."""
        if not name and roles == []:
            raise TypeError("one of 'name' or 'roles' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'roles': roles
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/emojis/{emoji_id}',
                guild_id=int(guild), emoji_id=int(emoji)
            ),
            json=payload, reason=reason
        )

    async def delete_emoji(
        self,
        guild: int,
        emoji: int,
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Delete an emoji from a guild."""
        return await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/emojis/{emoji_id}',
                guild_id=int(guild), emoji_id=int(emoji)
            ),
            reason=reason
        )

    # Guild endpoints

    async def create_guild(
        self,
        name: str,
        *,
        icon: str = MISSING,
        verification_level: int = MISSING,
        notification_level: int = MISSING,
        content_filter: int = MISSING,
        roles: Sequence[Any] = MISSING,
        channels: Sequence[Any] = MISSING,
        afk_channel: int = MISSING,
        afk_timeout: int = MISSING,
        system_channel: int = MISSING,
        system_channel_flags: int = MISSING
    ) -> Dict[str, Any]:
        """Create a new guild, making the bot the owner."""
        payload: Dict[str, Any] = {
            'name': name,
            'icon': icon,
            'verification_level': verification_level,
            'default_message_notifications': notification_level,
            'explicit_content_filter': content_filter,
            'roles': roles,
            'channels': channels,
            'afk_channel_id': afk_channel,
            'afk_timeout': afk_timeout,
            'system_channel_id': system_channel,
            'system_channel_flags': system_channel_flags
        }

        return await self.request(Route('POST', '/guilds'), json=payload)

    async def fetch_guild(self, guild: int, *, with_counts: bool = False) -> Dict[str, Any]:
        """Fetch a guild by its ID.

        If `with_counts` is set, an approximate member count will be included.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_guild_preview(self, guild: int) -> Dict[str, Any]:
        """Fetch a preview of a guild by its ID.

        If the bot user is not in the guild, it must be lurkable. Meaning that
        it must be discoverable or have a live public stage.
        """
        return await self.request(Route('GET', '/guilds/{guild_id}/preview', guild_id=int(guild)))

    async def edit_guild(
        self,
        guild: int,
        *,
        name: str = MISSING,
        verification_level: Optional[int] = MISSING,
        notification_level: Optional[int] = MISSING,
        content_filter: Optional[int] = MISSING,
        afk_channel: Optional[int] = MISSING,
        afk_timeout: Optional[int] = MISSING,
        icon: Optional[str] = MISSING,
        owner: int = MISSING,
        splash: Optional[str] = MISSING,
        discovery: Optional[str] = MISSING,
        banner: Optional[str] = MISSING,
        system_channel: Optional[int] = MISSING,
        system_channel_flags: int = MISSING,
        rules_channel: Optional[int] = MISSING,
        updates_channel: Optional[int] = MISSING,
        preferred_locale: Optional[str] = MISSING,
        features: Sequence[str] = MISSING,
        description: Optional[str] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild."""
        payload: Dict[str, Any] = {
            'name': name,
            'verification_level': verification_level,
            'default_message_notifications': notification_level,
            'explicit_content_filter': content_filter,
            'afk_channel_id': int(afk_channel) if afk_channel else afk_channel,
            'afk_timeout': afk_timeout,
            'icon': icon,
            'owner_id': int(owner) if owner else owner,
            'splash': splash,
            'disconvery_splash': discovery,
            'banner': banner,
            'system_channel_id': int(system_channel) if system_channel else system_channel,
            'system_channel_flags': system_channel_flags,
            'rules_channel_id': int(rules_channel) if rules_channel else rules_channel,
            'public_updates_channel_id': int(updates_channel) if updates_channel else updates_channel,
            'preferred_locale': preferred_locale,
            'features': features,
            'description': description
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def delete_guild(self, guild: int) -> None:
        """Delete a guild permanently, the bot must be the owner."""
        await self.request(Route('DELETE', '/guilds/{guild_id}', guild_id=int(guild)))

    async def fetch_guild_channels(self, guild: int) -> List[Any]:
        """Fetch all channels in a guild, excluding threads."""
        return await self.request(Route('GET', '/guilds/{guild_id}/channels', guild_id=int(guild)))

    async def create_channel(
        self,
        guild: int,
        name: str,
        *,
        type: int = MISSING,
        topic: str = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rate_limit: int = MISSING,
        position: int = MISSING,
        permission_overwrites: List[PermissionOverwrite] = MISSING,
        parent: int = MISSING,
        nsfw: bool = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new guild channel."""
        payload: Dict[str, Any] = {
            'name': name,
            'type': type,
            'topic': topic,
            'bitrate': bitrate,
            'user_limit': user_limit,
            'rate_limit_per_user': rate_limit,
            'position': position,
            'permissin_overwrites': permission_overwrites,
            'parent_id': int(parent) if parent else parent,
            'nsfw': nsfw,
        }

        return await self.request(
            Route('POST', '/guilds/{guild_id}/channels', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_channel_positions(
        self,
        guild: int,
        channels: List[Dict[str, Any]],
        *,
        reason: str = MISSING
    ) -> None:
        """Edit several channels' positions."""
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/channels', guild_id=int(guild)),
            json=channels, reason=reason
        )

    async def fetch_active_threads(self, guild: int) -> Dict[str, Any]:
        """Fetch all active threads in a guild, both public and private threads."""
        return await self.request(
            Route('GET', '/guilds/{guild_id}/threads/active', guild_id=int(guild))
        )

    async def fetch_member(self, guild: int, user: int) -> Dict[str, Any]:
        """Fetch a specific member object by its user ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/embers/{user_id}',
            guild_id=int(guild), user_id=int(user)
        ))

    async def fetch_members(
        self,
        guild: int,
        *,
        limit: int = 1,
        after: int = 0
    ) -> List[Any]:
        """Fetch all members in a guild.

        `after` is the highest user ID in the previous page, this way you can
        paginate all members even the guild has more than 1000 members.
        """
        if 0 > limit > 1001:
            raise TypeError("'limit' must be a value between 1-1000")

        return await self.request(
            Route('GET', '/guilds/{guild_id}/members', guild_id=int(guild)),
            params={'limit': limit, 'after': after}
        )

    async def search_members(self, guild: int, query: str, *, limit: int = 1) -> List[Any]:
        """Search guild members after a name or nickname similar to `query`."""
        return await self.request(
            Route('GET', '/guilds/{guild_id}/members/search', guild_id=int(guild)),
            params={'query': query, 'limit': limit}
        )

    async def edit_member(
        self,
        guild: int,
        user: int,
        *,
        nick: Optional[str] = MISSING,
        roles: Optional[List[int]] = MISSING,
        mute: Optional[bool] = MISSING,
        deafen: Optional[bool] = MISSING,
        channel: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit another guild member."""
        payload: Dict[str, Any] = {
            'nick': nick,
            'roles': roles,
            'mute': mute,
            'deaf': deafen,
            'channel_id': int(channel) if channel else channel
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/members/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ),
            json=payload, reason=reason
        )

    async def edit_my_nick(
        self,
        guild: int,
        nick: Optional[str] = '',
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit the nickname of the bot in the guild, passing None will reset the nickname."""
        # We need to mimic Discord's API, if you don't pass `nick` nothing happens
        options: Dict[str, Any] = {}
        if nick != '':
            options['nick'] = nick

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/members/@me/nick', guild_id=int(guild)),
            json=options, reason=reason
        )

    async def add_member_role(
        self,
        guild: int,
        user: int,
        role: int,
        *,
        reason: str = MISSING
    ) -> None:
        """Add a role to a guild member."""
        await self.request(
            Route(
                'PUT', '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                guild_id=int(guild), user_id=int(user), role_id=int(role)
            ), reason=reason
        )

    async def remove_member_role(
        self,
        guild: int,
        user: int,
        role: int,
        *,
        reason: str = MISSING
    ) -> None:
        """Remove a role from a guild member."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
                guild_id=int(guild), user_id=int(user), role_id=int(role)
            ), reason=reason
        )

    async def kick_member(self, guild: int, user: int, *, reason: str = MISSING) -> None:
        """Remove a member from a guild, also known as kicking a member."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/members/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_bans(self, guild: int) -> List[Any]:
        """Fetch all bans made on a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/bans', guild_id=int(guild)))

    async def fetch_ban(self, guild: int, user: int) -> Dict[str, Any]:
        """Fetch a specific ban made for a user."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/bans/{user_id}',
            guild_id=int(guild), user_id=int(user)
        ))

    async def ban_member(
        self,
        guild: int,
        user: int,
        *,
        delete_message_days: int = MISSING,
        reason: str = MISSING
    ) -> None:
        """Create a guild ban, and ban a specific user from re-entering the guild."""
        options: Dict[str, Any] = {}
        if delete_message_days is not MISSING:
            options['delete_message_days'] = delete_message_days

        await self.request(
            Route(
                'PUT', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ),
            json=options, reason=reason
        )

    async def pardon_user(self, guild: int, user: int, *, reason: str = MISSING) -> None:
        """Pardon a user, and remove the ban allowing them to enter the guild again."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/bans/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), reason=reason
        )

    async def fetch_roles(self, guild: int) -> List[Any]:
        """Fetch all roles from a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/roles', guild_id=int(guild)))

    async def create_role(
        self,
        guild: int,
        *,
        name: str = "new role",
        permissions: Union[str, int] = MISSING,
        color: int = 0,
        hoist: bool = False,
        mentionable: bool = False,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new role in a guild."""
        payload: Dict[str, Any] = {
            'name': name,
            'permissions': str(permissions) if permissions else MISSING,
            'color': color,
            'hoist': hoist,
            'mentionable': mentionable
        }

        return await self.request(
            Route('POST', '/guilds/{guild_id}/roles', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def edit_role_positions(
        self,
        guild: int,
        roles: List[Dict[str, Any]],
        reason: str = MISSING
    ) -> List[Any]:
        """Edit several roles' positions."""
        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/roles', guild_id=int(guild)),
            json=roles, reason=reason
        )

    async def edit_guild_role(
        self,
        guild: int,
        role: int,
        *,
        name: Optional[str] = MISSING,
        permissions: Optional[Union[int, str]] = MISSING,
        color: Optional[int] = MISSING,
        hoist: Optional[bool] = MISSING,
        mentionable: Optional[bool] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild role's different fields."""
        payload: Dict[str, Any] = {
            'name': name,
            'permissions': str(permissions) if permissions else permissions,
            'color': color,
            'hoist': hoist,
            'mentionable': mentionable
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/roles/{role_id}',
                guild_id=int(guild), role_id=int(role)
            ),
            json=payload, reason=reason
        )

    async def delete_role(self, guild: int, role: int, *, reason: str = MISSING) -> None:
        """Delete a guild role."""
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/roles/{role_id}',
                guild_id=int(guild), role_id=int(role)
            ), reason=reason
        )

    async def fetch_guild_prune_count(
        self,
        guild: int,
        *,
        days: int = 7,
        roles: Optional[Sequence[int]] = None
    ) -> Dict[str, int]:
        """Fetch the amount of members that would be pruned.

        `roles` is a list of roles that should be included, as normally
        any member with roles is excluded from the operation.
        """
        # Roles may be a list of role object, first we int() them for the IDs
        # and then convert them to strings to join them
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        return await self.request(
            Route('GET', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            params={'days': days, 'include_roles': include_roles}
        )

    async def prune_guild(
        self,
        guild: int,
        *,
        days: int = 7,
        compute_count: bool = True,
        roles: Optional[Sequence[int]] = None,
        reason: str = MISSING
    ) -> Dict[str, Optional[int]]:
        """Begin a prune operation, and kick all members who do not meet the criteria passed."""
        include_roles = ', '.join([str(int(r)) for r in roles]) if roles else roles
        return await self.request(
            Route('POST', '/guilds/{guild_id}/prune', guild_id=int(guild)),
            json={'days': days, 'compute_prune_count': compute_count, 'include_roles': include_roles},
            reason=reason
        )

    async def fetch_voice_regions(self, guild: int = MISSING) -> List[Any]:
        """Fetch a list of voice regions.

        If a guild is passed, this may return VIP servers if the guild
        is VIP-enabled.
        """
        if guild is MISSING:
            return await self.request(Route('GET', '/voice/regions'))

        return await self.request(Route('GET', '/guilds/{guild_id}/regions', guild_id=int(guild)))

    async def fetch_invites(self, guild: int) -> List[Any]:
        """Fetch all invites for the guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=int(guild)))

    async def fetch_integrations(self, guild: int) -> List[Any]:
        """Fetch all intergration for the guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/integrations', guild_id=int(guild)))

    async def delete_integration(
        self,
        guild: int,
        integration: int,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete an attached integration for the guild.

        This may also delete any associated webhooks and kick the bot if
        there is one attached.
        """
        await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/integrations/{integration_id}',
                guild_id=int(guild), integration_id=int(integration)
            ), reason=reason
        )

    async def fetch_widget_settings(self, guild: int) -> Dict[str, Any]:
        """Fetch the settings for a widget for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/widget', guild_id=int(guild)))

    async def edit_widget(
        self,
        guild: int,
        *,
        enabled: bool = MISSING,
        channel: Optional[int] = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild widget."""
        payload: Dict[str, Any] = {
            'enabled': enabled,
            'channel_id': int(channel) if channel else channel
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/widget', guild_id=int(guild)),
            json=payload, reason=reason
        )

    async def fetch_widget(self, guild: int) -> Dict[str, Any]:
        """Fetch a complete widget for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/widget.json', guild_id=int(guild)))

    async def fetch_vanity_invite(self, guild: int) -> Dict[str, Any]:
        """Fetch a partial invite for a guild that has that feature."""
        return await self.request(Route('GET', '/guilds/{guild_id}/vanity-url', guild_id=int(guild)))

    async def fetch_widget_image(
        self,
        guild: int,
        *,
        style: Literal['shield', 'banner1', 'banner2', 'banner3', 'banner4'] = 'shield'
    ) -> bytes:
        """Read a style of PNG image for a guild's widget."""
        return await self._bypass_request(
            'GET',
            Route.BASE + f'/guilds/{int(guild)}/widget.png',
            style=style
        )

    async def fetch_welcome_screen(self, guild: int) -> Dict[str, Any]:
        """Fetch the welcome screen for a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/welcome-screen', guild_id=int(guild)))

    async def edit_welcome_screen(
        self,
        guild: int,
        *,
        enabled: Optional[bool] = MISSING,
        welcome_channels: List[Dict[str, Any]] = MISSING,
        description: Optional[str] = MISSING
    ) -> Dict[str, Any]:
        """Edit the guild's welcome screen."""
        if enabled is MISSING and welcome_channels is MISSING and description is MISSING:
            raise TypeError("one of 'enabled', 'welcome_channels' or 'description' is requied")

        payload: Dict[str, Any] = {
            'enabled': enabled,
            'welcome_channels': welcome_channels,
            'description': description
        }

        return await self.request(
            Route('PATCH', '/guilds/{guild_id}/welcome-screen', guild_id=int(guild)),
            json=payload
        )

    async def edit_my_voice_state(
        self,
        guild: int,
        *,
        channel: int,
        suppress: bool = MISSING,
        request_to_speak: int = MISSING
    ) -> Dict[str, Any]:
        """Update the bot user's voice state in that guild."""
        options: Dict[str, Any] = {'channel_id': int(channel)}
        if suppress is not MISSING:
            options['suppress'] = suppress

        if request_to_speak is not MISSING:
            options['request_to_speak_timestamp'] = request_to_speak

        return await self.request(
            Route('PATCH', 'guild/{guild_id}/voice-states/@me', guild_id=int(guild)),
            json=options
        )

    async def edit_voice_state(
        self,
        guild: int,
        user: int,
        *,
        channel: int,
        suppress: bool = MISSING
    ) -> Dict[str, Any]:
        """Edit another user's voice state."""
        options: Dict[str, Any] = {'channel': int(channel)}
        if suppress is not MISSING:
            options['suppress'] = suppress

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/voice-states/{user_id}',
                guild_id=int(guild), user_id=int(user)
            ), json=options
        )

    # Guild Template endpoints

    async def fetch_guild_template(self, code: str) -> Dict[str, Any]:
        """Fetch a guild template by its code."""
        return await self.request(Route(
            'GET', '/guilds/templates/{template_code}', template_code=str(code)
        ))

    async def create_guild_from_template(
        self,
        template: str,
        *,
        name: str,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new guild based on a template."""
        return await self.request(
            Route('POST', '/guilds/templates/{template_code}', template_code=str(template)),
            json={'name': name, 'icon': icon}
        )

    async def fetch_guild_templates(self, guild: int) -> List[Any]:
        """Fetch a list of all guild templates created from a guild."""
        return await self.request(Route('GET', '/guilds/{guild_id}/templates', guild_id=int(guild)))

    async def create_guild_template(
        self,
        guild: int,
        *,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a template from a guild."""
        return await self.request(
            Route('POST', '/guilds/{guild_id}/templates', guild_id=int(guild)),
            json={'name': name, 'description': description}
        )

    async def sync_guild_template(self, guild: int, template: str) -> Dict[str, Any]:
        """Sync the template with the guild's current state."""
        return await self.request(Route(
            'PUT', '/guilds/{guild_id}/templates/{template_code}',
            guild_id=int(guild), template_code=str(template)
        ))

    async def edit_guild_template(
        self,
        guild: int,
        template: str,
        *,
        name: str = MISSING,
        description: str = MISSING
    ) -> Dict[str, Any]:
        """Edit the guild template's metadata."""
        if name is MISSING and description is MISSING:
            raise TypeError("at least one of 'name' or 'description' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'description': description
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/templates/{template_code}',
                guild_id=int(guild), template_code=str(template)
            ), json=payload
        )

    async def delete_guild_template(self, guild: int, template: str) -> Dict[str, Any]:
        """Delete the guild template by its code."""
        return await self.request(Route(
            'DELETE', '/guilds/{guild_id}/templates/{template_code}',
            guild_id=int(guild), template_code=str(template)
        ))

    # Invite endpoints

    async def fetch_invite(self, code: str) -> Dict[str, Any]:
        """Fetch invite information by its code."""
        return await self.request(Route('GET', '/invites/{invite_code}', invite_code=str(code)))

    async def delete_invite(self, code: str, *, reason: str = MISSING) -> Dict[str, Any]:
        """Delete an invite by its code, this requires certain permissions."""
        return await self.request(
            Route(
                'DELETE', '/invites/{invite_code}', invite_code=str(code)
            ), reason=reason
        )

    # Stage Instance endpoints

    async def create_stage_instance(
        self,
        channel: int,
        topic: str,
        privacy_level: int = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new stage instance associated with a stage channel."""
        payload: Dict[str, Any] = {
            'channel_id': int(channel),
            'topic': topic,
            'privacy_level': privacy_level,
        }

        return await self.request(
            Route('POST', '/stage-instances'),
            json=payload, reason=reason
        )

    async def fetch_stage_instance(self, channel: int) -> Dict[str, Any]:
        """Fetch the stage instance associated with the stage channel, if it exists."""
        return await self.request(Route(
            'GET', '/stage-instances/{channel_id}', channel_id=int(channel)
        ))

    async def edit_stage_instance(
        self,
        channel: int,
        *,
        topic: str = MISSING,
        privacy_level: int = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit fields of an existing stage instance."""
        if topic is MISSING and privacy_level is MISSING:
            raise TypeError("at least one of 'topic' or 'privacy_level' is required")

        payload: Dict[str, Any] = {
            'topic': topic,
            'privacy_level': privacy_level
        }

        return await self.request(
            Route('PATCH', '/stage-instances/{channel_id}', channel_id=int(channel)),
            json=payload, reason=reason
        )

    async def delete_stage_instance(
        self,
        channel: int,
        *,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Delete a stage instance by its ID."""
        return await self.request(
            Route('DELETE', '/stage-instances/{channel_id}', channel_id=int(channel)),
            reason=reason
        )

    # Sticker endpoints

    async def fetch_sticker(self, sticker: int) -> Dict[str, Any]:
        """Fetch a sticker by its ID."""
        return await self.request(Route('GET', '/stickers/{sticker_id}', sticker_id=int(sticker)))

    async def fetch_nitro_sticker_packs(self) -> Dict[str, Any]:
        """Fetch a list of all sticker packs currently available to Nitro subscribers."""
        return await self.request(Route('GET', '/sticker-packs'))

    async def fetch_guild_stickers(self, guild: int) -> List[Any]:
        """Fetch all stickers for a guild by its ID."""
        return await self.request(Route('GET', '/guilds/{guild_id}/stickers', guild_id=int(guild)))

    async def fetch_guild_sticker(self, guild: int, sticker: int) -> Dict[str, Any]:
        """Fetch a sticker from a guild given its ID."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/stickers/{sticker_id}',
            guild_id=int(guild), sticker_id=int(sticker)
        ))

    async def create_sticker(
        self,
        guild: int,
        *,
        name: str,
        description: str,
        tags: str,
        file: File,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Create a new sticker for a guild."""
        data = {
            'name': name,
            'description': description,
            'tags': tags,
            'file': file
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/stickers', guild_id=int(guild)),
            data=data, reason=reason
        )

    async def edit_guild_sticker(
        self,
        guild: int,
        sticker: int,
        *,
        name: str = MISSING,
        description: str = MISSING,
        tags: str = MISSING,
        reason: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a guild sticker by its ID."""
        if name is MISSING and description is MISSING and tags is MISSING:
            raise TypeError("at least one of 'name', 'description' or 'tags is required")

        payload: Dict[str, Any] = {
            'name': name,
            'description': description,
            'tags': tags,
        }

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            json=payload, reason=reason
        )

    async def delete_guild_sticker(
        self,
        guild: int,
        sticker: int,
        *,
        reason: str = MISSING
    ) -> None:
        """Delete a guild sticker by its ID."""
        return await self.request(
            Route(
                'DELETE', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            reason=reason
        )

    # User endpoints

    async def fetch_my_user(self) -> Dict[str, Any]:
        """Fetch the bot user account.

        This is not a shortcut to `fetch_user()`, it has a different ratelimit
        and returns a bit more information.
        """
        return await self.request(Route('GET', '/users/@me'))

    async def fetch_user(self, user: int) -> Dict[str, Any]:
        """Fetch a user by its ID.

        You do not need to share a guild with the user to fetch their
        (limited) information.
        """
        return await self.request(Route('GET', '/users/{user_id}', user_id=int(user)))

    async def edit_my_user(
        self,
        *,
        username: str = MISSING,
        avatar: str = MISSING,
    ) -> Dict[str, Any]:
        """Edit the bot user account.

        `avatar` is an optional string, passing None will set the user's avatar
        to its default avatar.
        """
        if username is MISSING and avatar is MISSING:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        payload: Dict[str, Any] = {
            'username': username,
            'avatar': avatar,
        }

        return await self.request(Route('PATCH', '/users/@me'), json=payload)

    async def fetch_my_guilds(self) -> List[Dict[str, Any]]:
        """Fetch all guilds that the bot user is in."""
        return await self.request(Route('GET', '/users/@me/guilds'))

    async def leave_guild(self, guild: int) -> None:
        """Make the bot user leave the specified guild."""
        await self.request(Route('DELETE', '/users/@me/guilds/{guild_id}', guild_id=int(guild)))

    async def create_dm(self, recipient: int) -> Dict[str, Any]:
        """Create a DM with the recipient.

        This method is safe to call several times to get the DM channel when
        needed. In fact, in other wrappers this is called everytime you send
        a message to a user.
        """
        return await self.request(Route(
            'POST', '/users/@me/channels'), json={'recipient_id': int(recipient)}
        )

    # Webhook endpoints (without usage of webhook token)

    async def create_webhook(
        self, channel: int, *, name: str, avatar: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new webhook.

        `name` follows some restrictions imposed by Discord, for example it
        cannot be 'clyde'. If `avatar` is None a default Discord avatar will
        be used.
        """
        return await self.request(
            Route('POST', '/channels/{channel_id}/webhooks', channel_id=int(channel)),
            json={'name': name, 'avatar': avatar}
        )

    async def fetch_channel_webhooks(self, channel: int) -> List[Dict[str, Any]]:
        """Fetch all webhooks for a channel."""
        return await self.request(Route(
            'GET', '/channels/{channel_id}/webhooks', channel_id=int(channel)
        ))

    async def fetch_guild_webhooks(self, guild: int) -> List[Dict[str, Any]]:
        """Fetch all webhooks for a comlete guild."""
        return await self.request(Route(
            'GET', '/guilds/{guild_id}/webhooks', guild_id=int(guild)
        ))

    async def fetch_webhook(self, webhook: int, token: str = MISSING) -> Dict[str, Any]:
        """Fetch a specific webhook by its id.

        This wraps both `/webhooks/{webhook.id}` and
        `webhooks/{webhook.id}/{webhook.token}` depending on what is passed.
        """
        if token is not MISSING:
            return await super().fetch_webhook(webhook, token)

        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}', webhook_id=int(webhook)
        ))

    @overload
    async def edit_webhook(
        self,
        webhook: int,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
        channel: int = MISSING
    ) -> Dict[str, Any]:
        ...

    @overload
    async def edit_webhook(
        self,
        webhook: int,
        token: str,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
    ) -> Dict[str, Any]:
        ...

    async def edit_webhook(
        self,
        webhook: int,
        token: str = MISSING,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
        channel: int = MISSING
    ) -> Dict[str, Any]:
        """Edit a webhook's fields.

        If `token` is passed the `/webhooks/{webhook.id}/{webhook.token}`
        variant will be used, this means that the user object will be missing
        from the webhook object and you cannot pass `channel`.
        """
        if token is not MISSING:
            return await super().edit_webhook(webhook, token, name=name, avatar=avatar)

        if name is MISSING and avatar is MISSING and channel is MISSING:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'avatar': avatar,
            'channel_id': channel
        }

        return await self.request(
            Route('PATCH', 'webhooks/{webhook_id}', webhook_id=int(webhook)), json=payload)

    async def delete_webhook(self, webhook: int, token: str = MISSING) -> None:
        """Delete a webhook by its ID."""
        if token is not MISSING:
            return await super().delete_webhook(webhook, token)

        await self.request(Route('DELETE', 'webhooks/{webhook_id}', webhook_id=int(webhook)))
