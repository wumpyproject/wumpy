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
