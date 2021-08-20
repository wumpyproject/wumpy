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

        options: Dict[str, Any] = {}
        if name is not MISSING:
            options['name'] = name

        if type is not MISSING:
            options['type'] = type

        if position is not MISSING:
            options['position'] = position

        if topic is not MISSING:
            options['topic'] = topic

        if nsfw is not MISSING:
            options['nsfw'] = nsfw

        if rate_limit is not MISSING:
            options['rate_limit_per_user'] = rate_limit

        if bitrate is not MISSING:
            options['bitrate'] = bitrate

        if user_limit is not MISSING:
            options['user_limit'] = user_limit

        if permission_overwrites is not MISSING:
            options['permission_overwrites'] = permission_overwrites

        if parent is not MISSING:
            options['parent_id'] = parent

        if rtc_region is not MISSING:
            options['rtc_region'] = rtc_region

        if video_quality is not MISSING:
            options['video_quality_mode'] = video_quality

        if default_auto_archive is not MISSING:
            options['default_auto_archive_duration'] = default_auto_archive

        return await self.request(
            Route('PATCH', '/channels/{channel_id}', channel_id=int(channel)),
            json=options, reason=reason
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

        options: Dict[str, Any] = {'limit': limit}
        if before is not MISSING:
            options['before'] = before

        if after is not MISSING:
            options['after'] = after

        if around is not MISSING:
            options['around'] = around

        return await self.request(
            Route('GET', '/channels/{channel_id}/messages', channel_id=int(channel)),
            params=options
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

        params: Dict[str, Any] = {}
        if wait is not MISSING:
            params['wait'] = wait

        if thread is not MISSING:
            params['thread_id'] = int(thread)

        json: Dict[str, Any] = {}
        if content is not MISSING:
            json['content'] = content

        if username is not MISSING:
            json['username'] = username

        if avatar_url is not MISSING:
            json['avatar_url'] = str(avatar_url)

        if tts is not MISSING:
            json['tts'] = tts

        if embeds is not MISSING:
            json['embeds'] = embeds

        if allowed_mentions is not MISSING:
            json['allowed_mentions'] = allowed_mentions._data

        if stickers is not MISSING:
            json['sticker_ids'] = [int(s) for s in stickers]

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
            data=data, params=params
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
        json: Dict[str, Any] = {}
        if content is not MISSING:
            json['content'] = content

        if embeds is not MISSING:
            json['embeds'] = embeds

        if allowed_mentions is not MISSING:
            json['allowed_mentions'] = allowed_mentions._data if allowed_mentions else None

        if attachments is not MISSING:
            json['attachments'] = attachments

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
        options: Dict[str, Any] = {
            'allow': str(allow),
            'deny': str(deny),
            'type': type
        }
        await self.request(
            Route(
                'PUT', '/channels/{channel_id}/permissions/{overwrite_id}',
                channel_id=int(channel), overwrite_id=int(overwrite)
            ),
            json=options, reason=reason
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

        options: Dict[str, Any] = {
            'max_age': max_age,
            'max_uses': max_uses,
            'temporary': temporary,
            'unique': unique
        }

        if target_type == 1:
            options['target_type'] = target_type
            options['target_user_id'] = target

        elif target_type == 2:
            options['target_type'] = target_type
            options['target_application_id'] = target

        return await self.request(
            Route(
                'POST', '/channels/{channel_id}/invites',
                channel_id=int(channel)
            ), reason=reason, json=options
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

        options: Dict[str, Any] = {
            'name': name,
            'auto_archive_duration': archive_duration
        }

        if message is not MISSING:
            path += '/messages/{message_id}'
            params['message_id'] = int(message)

            options['type'] = type
            if invitable is not MISSING:
                options['invitable'] = invitable

        return await self.request(
            Route('POST', path + '/threads', **params),
            json=options, reason=reason
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

    async def fetch_active_threads(self, channel: int) -> Dict[str, Any]:
        """Fetch all actie threads in a channel, both public and private threads."""
        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/active', channel_id=int(channel))
        )

    async def fetch_public_archived_threads(
        self,
        channel: int,
        *,
        before: int = MISSING,
        limit: int = MISSING,
    ) -> Dict[str, Any]:
        """Fetch all archived public threads."""
        query: Dict[str, Any] = {}
        if before is not MISSING:
            query['before'] = before

        if limit is not MISSING:
            query['limit'] = limit

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
        query: Dict[str, Any] = {}
        if before is not MISSING:
            query['before'] = before

        if limit is not MISSING:
            query['limit'] = limit

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
        query: Dict[str, Any] = {}
        if before is not MISSING:
            query['before'] = before

        if limit is not MISSING:
            query['limit'] = limit

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
        data = {
            'name': name,
            'image': image,
            # We can't iterate through None, so we need to add an additional
            # gate so that we simply pass None if it is
            'roles': [int(r) for r in roles] if roles else None
        }
        return await self.request(
            Route('POST', '/guilds/{guild_id}/emojis', guild_id=int(guild)),
            data=data, reason=reason
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

        options: Dict[str, Any] = {}
        if name is not MISSING:
            options['name'] = name

        if roles is not MISSING:
            options['roles'] = roles

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/emojis/{emoji_id}',
                guild_id=int(guild), emoji_id=int(emoji)
            ),
            json=options, reason=reason
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

        options: Dict[str, Any] = {}
        if name is not MISSING:
            options['name'] = name

        if description is not MISSING:
            options['description'] = description

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/templates/{template_code}',
                guild_id=int(guild), template_code=str(template)
            ), json=options
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
        options: Dict[str, Any] = {
            'channel_id': int(channel),
            'topic': topic
        }

        if privacy_level is not MISSING:
            options['privacy_level'] = privacy_level

        return await self.request(
            Route('POST', '/stage-instances'),
            json=options, reason=reason
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

        options: Dict[str, Any] = {}

        if topic is not MISSING:
            options['topic'] = topic

        if privacy_level is not MISSING:
            options['privacy_level'] = privacy_level

        return await self.request(
            Route('PATCH', '/stage-instances/{channel_id}', channel_id=int(channel)),
            json=options, reason=reason
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

        options: Dict[str, Any] = {}
        if name is not MISSING:
            options['name'] = name

        if description is not MISSING:
            options['description'] = description

        if tags is not MISSING:
            options['tags'] = tags

        return await self.request(
            Route(
                'PATCH', '/guilds/{guild_id}/stickers/{sticker_id}',
                guild_id=int(guild), sticker_id=int(sticker)
            ),
            json=options, reason=reason
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

        params: Dict[str, Any] = {}
        if username is not MISSING:
            params['username'] = username

        if avatar is not MISSING:
            params['avatar'] = avatar

        return await self.request(Route('PATCH', '/users/@me'), json=params)

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

    # Voice endpoints

    async def fetch_voice_regions(self) -> List[Dict[str, Any]]:
        """Fetch all available voice regions.

        This can be useful for when creating voice channels or guilds.
        """
        return await self.request(Route('GET', '/voice/regions'))

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

        body: Dict[str, Any] = {}
        if name is not MISSING:
            body['name'] = name

        if avatar is not MISSING:
            body['avatar'] = avatar

        if channel is not MISSING:
            body['channel_id'] = channel

        return await self.request(
            Route('PATCH', 'webhooks/{webhook_id}', webhook_id=int(webhook)), json=body)

    async def delete_webhook(self, webhook: int, token: str = MISSING) -> None:
        """Delete a webhook by its ID."""
        if token is not MISSING:
            return await super().delete_webhook(webhook, token)

        await self.request(Route('DELETE', 'webhooks/{webhook_id}', webhook_id=int(webhook)))
