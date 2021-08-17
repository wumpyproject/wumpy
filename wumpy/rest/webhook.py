from typing import Any, Dict, Optional, Sequence

from ..models import Object, AllowedMentions
from .requester import Route, Requester
from .utils import File

__all__ = ('WebhookRequester', 'Webhook',)


class WebhookRequester(Requester):
    """Bare requester subclass for use of a standalone webhook."""

    async def fetch_webhook(self, webhook: int, token: str) -> Dict[str, Any]:
        """Fetch a specific webhook by its id with the token."""
        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ))

    async def edit_webhook(
        self,
        webhook: int,
        token: str,
        *,
        name: Optional[str] = None,
        avatar: Optional[str] = ''
    ) -> Dict[str, Any]:
        """Edit a webhook."""
        if not name or avatar == '':
            raise TypeError("at least one of 'username' or 'avatar' is required")

        body: Dict[str, Any] = {}
        if name:
            body['name'] = name

        if avatar != '':
            body['avatar'] = avatar

        return await self.request(Route(
            'PATCH', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ), json=body)

    async def delete_webhook(self, webhook: int, token: str) -> None:
        """Delete a webhook."""
        await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ))

    async def execute_webhook(
        self,
        webhook: int,
        token: str,
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
        """Execute a webhook, making it send a message in the channel it has been setup in."""

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
                'POST', '/webhooks/{webhook_id}/{webhook_token}}',
                webhook_id=int(webhook), webhook_token=token
            ),
            data=data
        )

    async def fetch_webhook_message(self, webhook: int, token: str, message: int) -> Dict[str, Any]:
        """Fetch a webhook's sent message."""
        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
        ))

    async def edit_webhook_message(
        self,
        webhook: int,
        token: str,
        message: int,
        *,
        content: Optional[str] = None,
        embeds: Optional[Sequence[Dict[str, Any]]] = None,
        file: Optional[File] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        attachments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Edit a webhook's sent message."""
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
                'PATCH', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
                webhook_id=int(webhook), webhook_token=token, message_id=int(message)
            ),
            data=data
        )

    async def delete_webhook_message(self, webhook: int, token: str, message: int) -> None:
        """Delete a webhook's sent message."""
        return await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
        ))


class Webhook(Object):
    """Standalone Discord webhook authorizing using a token."""

    def __init__(self, id: int, token: str, *, wait: bool = False) -> None:
        super().__init__(int(id))

        self.rest = WebhookRequester()

        self.token = token
        self.wait = wait

    async def fetch(self) -> Dict[str, Any]:
        """Fetch information about this webhook."""
        return await self.rest.fetch_webhook(self.id, self.token)

    async def edit(self, *, name: Optional[str] = None, avatar: Optional[str] = '') -> Dict[str, Any]:
        """Edit this webhook's `name` or `avatar`.

        An empty string is used as a sentinel value for `avatar`, passing
        None will cause the webhook to get its default Discord avatar.
        """
        return await self.rest.edit_webhook(self.id, self.token, name=name, avatar=avatar)

    async def delete(self) -> None:
        """Delete this webhook, it cannot be used after this has been called."""
        return await self.rest.delete_webhook(self.id, self.token)

    async def send_message(
        self,
        content: Optional[str] = None,
        *,
        wait: Optional[bool] = None,
        thread: Optional[int] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: Optional[bool] = None,
        embeds: Optional[Sequence[Dict[str, Any]]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        file: Optional[File] = None,
    ) -> Dict[str, Any]:
        """Send a message with this webhook."""
        if wait is None:
            wait = self.wait

        return await self.rest.execute_webhook(
            self.id, self.token, wait=wait, thread=thread, content=content,
            username=username, avatar_url=avatar_url, tts=tts, embeds=embeds,
            allowed_mentions=allowed_mentions, file=file
        )

    async def fetch_message(self, message: int) -> Dict[str, Any]:
        """Fetch a message this webhook has sent."""
        return await self.rest.fetch_webhook_message(
            self.id, self.token, message
        )

    async def edit_message(
        self,
        message: int,
        *,
        content: Optional[str] = None,
        embeds: Optional[Sequence[Dict[str, Any]]] = None,
        file: Optional[File] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        attachments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Edit a message this webhook has sent."""
        return await self.rest.edit_webhook_message(
            self.id, self.token, message, content=content, embeds=embeds,
            file=file, allowed_mentions=allowed_mentions, attachments=attachments
        )

    async def delete_message(self, message: int) -> None:
        """Delete a message this webhook has sent."""
        return await self.rest.delete_webhook_message(
            self.id, self.token, message
        )
