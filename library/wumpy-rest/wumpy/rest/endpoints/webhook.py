from typing import Any, Dict, Optional, Sequence, SupportsInt

from ..route import Route
from ..utils import MISSING, File
from .base import Requester


class WebhookRequester(Requester):
    """Bare requester subclass for use of a standalone webhook."""

    __slots__ = ()

    async def fetch_webhook(self, webhook: SupportsInt, token: str) -> Dict[str, Any]:
        """Fetch a specific webhook by its id with the token."""
        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ))

    async def edit_webhook(
        self,
        webhook: SupportsInt,
        token: str,
        *,
        name: str = MISSING,
        avatar: str = MISSING
    ) -> Dict[str, Any]:
        """Edit a webhook."""
        if name is MISSING and avatar is MISSING:
            raise TypeError("at least one of 'username' or 'avatar' is required")

        payload: Dict[str, Any] = {
            'name': name,
            'avatar': avatar
        }

        return await self.request(Route(
            'PATCH', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ), json=payload)

    async def delete_webhook(self, webhook: SupportsInt, token: str) -> None:
        """Delete a webhook."""
        await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ))

    async def execute_webhook(
        self,
        webhook: SupportsInt,
        token: str,
        *,
        wait: bool = False,
        thread: SupportsInt = MISSING,
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

        params: Dict[str, Any] = {
            'wait': wait,
            'thread_id': int(thread) if thread else MISSING,  # We cannot int() MISSING
        }

        json: Dict[str, Any] = {
            'content': content,
            'username': username,
            'avatar_url': str(avatar_url),
            'tts': tts,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else MISSING
        }

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = self._clean_dict(json)

        if file is not MISSING:
            data['file'] = file

        return await self.request(
            Route(
                'POST', '/webhooks/{webhook_id}/{webhook_token}}',
                webhook_id=int(webhook), webhook_token=token
            ),
            data=data, params=params
        )

    async def fetch_webhook_message(
        self,
        webhook: SupportsInt,
        token: str,
        message: SupportsInt
    ) -> Dict[str, Any]:
        """Fetch a webhook's sent message."""
        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
        ))

    async def edit_webhook_message(
        self,
        webhook: SupportsInt,
        token: str,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        file: Optional[File] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        attachments: Optional[Dict[str, Any]] = MISSING
    ) -> Dict[str, Any]:
        """Edit a webhook's sent message."""
        json: Dict[str, Any] = {
            'content': content,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else allowed_mentions,
            'attachments': attachments,
        }

        # This will cause HTTPx to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = self._clean_dict(json)

        if file is not MISSING:
            data['file'] = file

        return await self.request(
            Route(
                'PATCH', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
                webhook_id=int(webhook), webhook_token=token, message_id=int(message)
            ),
            data=data
        )

    async def delete_webhook_message(
        self,
        webhook: SupportsInt,
        token: str,
        message: SupportsInt
    ) -> None:
        """Delete a webhook's sent message."""
        return await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
