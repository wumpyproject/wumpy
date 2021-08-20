from typing import Any, Dict, Sequence

from ..models import AllowedMentions, Object
from ..utils import MISSING
from .requester import Requester, Route
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
        name: str = MISSING,
        avatar: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a webhook."""
        if name is MISSING and avatar is MISSING:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        body: Dict[str, Any] = {}
        if name is not MISSING:
            body['name'] = name

        if avatar is not MISSING:
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
        thread: int = MISSING,
        content: str = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
    ) -> Dict[str, Any]:
        """Execute a webhook, making it send a message in the channel it has been setup in."""

        if content is MISSING and embeds is MISSING and file is MISSING:
            raise TypeError("one of 'content', 'embeds' or 'file' is required")

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

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file is not MISSING:
            data['file'] = file

        return await self.request(
            Route(
                'POST', '/webhooks/{webhook_id}/{webhook_token}}',
                webhook_id=int(webhook), webhook_token=token
            ),
            data=data, params=params
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
        content: str = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        file: File = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        attachments: Dict[str, Any] = MISSING
    ) -> Dict[str, Any]:
        """Edit a webhook's sent message."""
        json: Dict[str, Any] = {}
        if content is not MISSING:
            json['content'] = content

        if embeds is not MISSING:
            json['embeds'] = embeds

        if allowed_mentions is not MISSING:
            json['allowed_mentions'] = allowed_mentions._data

        if attachments is not MISSING:
            json['attachments'] = attachments

        # This will cause aiohttp to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

        if file is not MISSING:
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

    async def edit(self, *, name: str = MISSING, avatar: str = MISSING) -> Dict[str, Any]:
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
        content: str = MISSING,
        *,
        wait: bool = MISSING,
        thread: int = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
    ) -> Dict[str, Any]:
        """Send a message with this webhook."""
        if wait is MISSING:
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
        content: str = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        file: File = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        attachments: Dict[str, Any] = MISSING
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
