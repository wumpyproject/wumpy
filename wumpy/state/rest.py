from typing import TYPE_CHECKING, Any, Dict, List, Optional, overload

from ..rest import Route, WebhookRequester

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
