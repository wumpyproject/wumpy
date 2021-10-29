"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, Dict, Optional, Sequence, SupportsInt

from ..models import AllowedMentions, Object
from ..utils import MISSING, File
from .requester import Requester, Route

__all__ = ('WebhookRequester', 'Webhook',)


class WebhookRequester(Requester):
    """Bare requester subclass for use of a standalone webhook."""

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
        params = self._clean_dict(params)

        json: Dict[str, Any] = {
            'content': content,
            'username': username,
            'avatar_url': str(avatar_url),
            'tts': tts,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else MISSING
        }
        json = self._clean_dict(json)

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
        json = self._clean_dict(json)

        # This will cause HTTPx to use multipart/form-data
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
        thread: SupportsInt = MISSING,
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

    async def fetch_message(self, message: SupportsInt) -> Dict[str, Any]:
        """Fetch a message this webhook has sent."""
        return await self.rest.fetch_webhook_message(
            self.id, self.token, message
        )

    async def edit_message(
        self,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        file: Optional[File] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        attachments: Optional[Dict[str, Any]] = MISSING
    ) -> Dict[str, Any]:
        """Edit a message this webhook has sent."""
        return await self.rest.edit_webhook_message(
            self.id, self.token, message, content=content, embeds=embeds,
            file=file, allowed_mentions=allowed_mentions, attachments=attachments
        )

    async def delete_message(self, message: SupportsInt) -> None:
        """Delete a message this webhook has sent."""
        return await self.rest.delete_webhook_message(
            self.id, self.token, message
        )
