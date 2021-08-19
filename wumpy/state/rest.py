from typing import Literal, TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union, overload
from urllib.parse import quote as urlquote

from ..models import AllowedMentions, PermissionOverwrite
from ..rest import File, Route, WebhookRequester

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
        name: Optional[str] = None,
        position: Optional[int] = ...,
        nsfw: Optional[bool] = None,
        permission_overwrites: Optional[List[PermissionOverwrite]] = [],
        parent: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit a Store channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: Optional[str] = None,
        position: Optional[int] = ...,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
        permission_overwrites: Optional[List[PermissionOverwrite]] = [],
        parent: Optional[int] = None,
        rtc_region: Optional[str] = None,
        video_quality: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit a Voice channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: Optional[str] = None,
        type: Optional[int] = None,
        position: Optional[int] = ...,
        topic: Optional[str] = None,
        nsfw: Optional[bool] = None,
        permission_overwrites: Optional[List[PermissionOverwrite]] = [],
        parent: Optional[int] = None,
        default_auto_archive: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit a News channel by its ID."""
        ...

    @overload
    async def edit_channel(
        self,
        channel: int,
        *,
        name: Optional[str] = None,
        type: Optional[int] = None,
        position: Optional[int] = ...,
        topic: Optional[str] = None,
        nsfw: Optional[bool] = None,
        rate_limit: Optional[int] = None,
        permission_overwrites: Optional[List[PermissionOverwrite]] = [],
        parent: Optional[int] = None,
        default_auto_archive: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit a Text channel by its ID."""
        ...

    async def edit_channel(
        self,
        channel: int,
        *,
        name: Optional[str] = None,
        type: Optional[int] = None,
        position: Optional[int] = -1,
        topic: Optional[str] = None,
        nsfw: Optional[bool] = None,
        rate_limit: Optional[int] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
        permission_overwrites: Optional[List[PermissionOverwrite]] = [],
        parent: Optional[int] = None,
        rtc_region: Optional[str] = None,
        video_quality: Optional[int] = None,
        default_auto_archive: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        # The amount of complexity necessary to ensure the user has passed a good
        # combination of options is too much for the library to bother at this moment

        options: Dict[str, Any] = {}
        if name:
            options['name'] = name

        if type:
            options['type'] = type

        if position != -1:
            options['position'] = position

        if topic:
            options['topic'] = topic

        if nsfw is not None:
            options['nsfw'] = nsfw

        if rate_limit is not None:
            options['rate_limit_per_user'] = rate_limit

        if bitrate:
            options['bitrate'] = bitrate

        if user_limit is not None:
            options['user_limit'] = user_limit

        if permission_overwrites is None or len(permission_overwrites) > 0:
            options['permission_overwrites'] = permission_overwrites

        if parent:
            options['parent_id'] = parent

        if rtc_region:
            options['rtc_region'] = rtc_region

        if video_quality:
            options['video_quality_mode'] = video_quality

        if default_auto_archive:
            options['default_auto_archive_duration'] = default_auto_archive

        return await self.request(
            Route('PATCH', '/channels/{channel_id}', channel_id=int(channel)),
            json=options, reason=reason
        )

    async def delete_channel(self, channel: int, *, reason: Optional[str] = None):
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
        before: Optional[int] = None,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        after: Optional[int] = None,
        limit: int = 50
    ) -> List[Any]:
        ...

    @overload
    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        around: Optional[int] = None,
        limit: int = 50
    ) -> List[Any]:
        ...

    async def fetch_channel_messages(
        self,
        channel: int,
        *,
        before: Optional[int] = None,
        after: Optional[int] = None,
        around: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Any]:
        """Fetch the messages for a channel by its ID."""
        if bool(before) + bool(after) + bool(around) > 1:
            raise TypeError("'before', 'after' and 'around' are mutually exclusive")
        elif limit and 0 > limit > 100:
            raise TypeError("'limit' must be a number between 1 and 100")

        options: Dict[str, Any] = {}
        if before:
            options['before'] = before

        if after:
            options['after'] = after

        if around:
            options['around'] = around

        if limit:
            options['limit'] = limit

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
        thread: Optional[int] = None,
        content: Optional[str] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: Optional[bool] = None,
        embeds: Optional[Sequence[Dict[str, Any]]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        file: Optional[File] = None,
    ) -> Dict[str, Any]:
        """Send a message into a channel."""

        if not content and not embeds and not file:
            raise TypeError("one of 'content', 'embeds' or 'file' is required")

        params: Dict[str, Any] = {}
        if wait:
            params['wait'] = wait

        if thread:
            params['thread_id'] = int(thread)

        json: Dict[str, Any] = {}
        if content:
            json['content'] = content

        if username:
            json['username'] = username

        if avatar_url:
            json['avatar_url'] = str(avatar_url)

        if tts:
            json['tts'] = tts

        if embeds:
            json['embeds'] = embeds

        if allowed_mentions:
            json['allowed_mentions'] = allowed_mentions._data

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file:
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
        user: Optional[int] = None
    ) -> None:
        """Delete a reaction, if no user is passed then the bot's own reaction is deleted."""
        # We int() user here so that we don't need to figure it out below
        target: Union[str, int] = '@me' if not user else int(user)

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

    async def clear_reactions(self, channel: int, message: int, emoji: Optional[str] = None) -> None:
        """Delete all reactions on a message.

        If an emojis is passed, only the reactions with that emojis are deleted.
        """
        path = '/channels/{channel_id}/messages/{message_id}/reactions'
        params: Dict[str, Any] = {'channel_id': int(channel), 'message_id': int(message)}

        if emoji:
            path += '/{emoji}'
            params['emoji'] = str(emoji)

        await self.request(Route('DELETE', path, **params))

    async def edit_message(
        self,
        channel: int,
        message: int,
        *,
        content: Optional[str] = None,
        embeds: Optional[Sequence[Dict[str, Any]]] = None,
        file: Optional[File] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        attachments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Edit a previously sent message."""
        json: Dict[str, Any] = {}
        if content:
            json['content'] = content

        if embeds:
            json['embeds'] = embeds

        if allowed_mentions:
            json['allowed_mentions'] = allowed_mentions._data

        if attachments:
            json['attachments'] = attachments

        # This will cause aiohttp to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file:
            data['file'] = file

        return await self.request(
            Route(
                'PATCH', '/channels/{channel_id}/messages/{message_id}',
                channel_id=int(channel), message_id=int(message)
            ),
            data=data
        )

    async def delete_message(self, channel: int, message: int, *, reason: Optional[str] = None) -> None:
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
        reason: Optional[str] = None
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
        reason: Optional[str] = None
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
        reason: Optional[str] = None
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
        reason: Optional[str] = None
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
        target_type: Optional[int] = None,
        target: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new channel invite.

        `target` wraps both `target_user_id` and `target_application_id` depending
        on what `target_type` is set.
        """
        if target_type and not target:
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

        if target_type == 2:
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
        reason: Optional[str] = None
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

    async def pin_message(self, channel: int, message: int, *, reason: Optional[str] = None) -> None:
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
        reason: Optional[str] = None
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
        reason: Optional[str] = None
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
        invitable: Optional[bool] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        ...

    async def start_thread(
        self,
        channel: int,
        message: Optional[int] = None,
        *,
        name: str,
        archive_duration: int,
        type: Optional[int] = None,
        invitable: Optional[bool] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new thread in a channel, with or without an existing message."""
        if not message and type:
            raise TypeError('thread type is required when starting a thread without a message')

        path = '/channels/{channel_id}'
        params: Dict[str, Any] = {'channel_id': int(channel)}

        options: Dict[str, Any] = {
            'name': name,
            'auto_archive_duration': archive_duration
        }

        if message:
            path += '/messages/{message_id}'
            params['message_id'] = int(message)

            options['type'] = type
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
        before: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch all archived public threads."""
        query: Dict[str, Any] = {}
        if before:
            query['before'] = before

        if limit:
            query['limit'] = limit

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )

    async def fetch_private_archived_threads(
        self,
        channel: int,
        *,
        before: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch all archived private threads."""
        query: Dict[str, Any] = {}
        if before:
            query['before'] = before

        if limit:
            query['limit'] = limit

        return await self.request(
            Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=int(channel)),
            params=query
        )

    async def fetch_joined_private_archived_threads(
        self,
        channel: int,
        *,
        before: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch all joined archived private threads."""
        query: Dict[str, Any] = {}
        if before:
            query['before'] = before

        if limit:
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
        roles: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an emoji in a guild."""
        data = {
            'name': name,
            'image': image,
            'roles': roles
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
        name: Optional[str] = None,
        roles: Optional[List[int]] = [],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit fields of an emoji by its ID.

        An empty list is used as a sentinel value for it missing.
        """
        if not name and roles == []:
            raise TypeError("one of 'name' or 'roles' is required")

        options: Dict[str, Any] = {}
        if name:
            options['name'] = name

        if roles != []:
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
        reason: Optional[str] = None
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
        name: Optional[str] = None,
        description: Optional[str] = ''
    ) -> Dict[str, Any]:
        """Edit the guild template's metadata."""
        if not name and description == '':
            raise TypeError("at least one of 'name' or 'description' is required")

        options: Dict[str, Any] = {}
        if name:
            options['name'] = name

        if description != '':
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

    async def delete_invite(self, code: str, *, reason: Optional[str] = None) -> Dict[str, Any]:
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
        privacy_level: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new stage instance associated with a stage channel."""
        options: Dict[str, Any] = {
            'channel_id': int(channel),
            'topic': topic
        }

        if privacy_level:
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
        topic: Optional[str] = None,
        privacy_level: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit fields of an existing stage instance."""
        if not topic and privacy_level is None:
            raise TypeError("at least one of 'topic' or 'privacy_level' is required")

        options: Dict[str, Any] = {}

        if topic:
            options['topic'] = topic

        if privacy_level is not None:
            options['privacy_level'] = privacy_level

        return await self.request(
            Route('PATCH', '/stage-instances/{channel_id}', channel_id=int(channel)),
            json=options, reason=reason
        )

    async def delete_stage_instance(
        self,
        channel: int,
        *,
        reason: Optional[str] = None
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
        reason: Optional[str] = None
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
        name: Optional[str] = None,
        description: Optional[str] = '',
        tags: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Edit a guild sticker by its ID.

        An empty string is used as a sentinel value, as passing None will cause
        the description to be removed.
        """
        if not name and description == '' and not tags:
            raise TypeError("at least one of 'name', 'description' or 'tags is required")

        options: Dict[str, Any] = {}
        if name:
            options['name'] = name

        if description != '':
            options['description'] = description

        if tags:
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
        reason: Optional[str] = None
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
        username: Optional[str] = None,
        avatar: Optional[str] = '',
    ) -> Dict[str, Any]:
        """Edit the bot user account.

        `avatar` is an optional string, passing None will set the user's avatar
        to its default avatar. An empty string is used as a sentinel value to
        know when an avatar was not passed.
        """
        if not username or avatar == '':
            raise TypeError("at least one of 'username' or 'avatar' is required")

        params: Dict[str, Any] = {}
        if username:
            params['username'] = username

        if avatar != '':
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

    async def fetch_webhook(self, webhook: int, token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch a specific webhook by its id.

        This wraps both `/webhooks/{webhook.id}` and
        `webhooks/{webhook.id}/{webhook.token}` depending on what is passed.
        """
        if token:
            return await super().fetch_webhook(webhook, token)

        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}', webhook_id=int(webhook)
        ))

    @overload
    async def edit_webhook(
        self,
        webhook: int,
        *,
        name: Optional[str] = None,
        avatar: Optional[str] = '',
        channel: Optional[int] = None
    ) -> Dict[str, Any]:
        ...

    @overload
    async def edit_webhook(
        self,
        webhook: int,
        token: Optional[str] = None,
        *,
        name: Optional[str] = None,
        avatar: Optional[str] = '',
    ) -> Dict[str, Any]:
        ...

    async def edit_webhook(
        self,
        webhook: int,
        token: Optional[str] = None,
        *,
        name: Optional[str] = None,
        avatar: Optional[str] = '',
        channel: Optional[int] = None
    ) -> Dict[str, Any]:
        """Edit a webhook's fields.

        If `token` is passed the `/webhooks/{webhook.id}/{webhook.token}`
        variant will be used, this means that the user object will be missing
        from the webhook object and you cannot pass `channel`.
        """
        if token:
            return await super().edit_webhook(webhook, token, name=name, avatar=avatar)

        if not name or avatar == '' or not channel:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        body: Dict[str, Any] = {}
        if name:
            body['name'] = name

        if avatar != '':
            body['avatar'] = avatar

        if channel:
            body['channel_id'] = channel

        return await self.request(
            Route('PATCH', 'webhooks/{webhook_id}', webhook_id=int(webhook)), json=body)

    async def delete_webhook(self, webhook: int, token: Optional[str] = None) -> None:
        """Delete a webhook by its ID."""
        if token:
            return await super().delete_webhook(webhook, token)

        await self.request(Route('DELETE', 'webhooks/{webhook_id}', webhook_id=int(webhook)))
