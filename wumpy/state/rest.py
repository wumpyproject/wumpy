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
    # Asset endpoint

    async def read_asset(self, url: str, *, size: int) -> bytes:
        return await self._bypass_request('GET', url, size=size)

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
