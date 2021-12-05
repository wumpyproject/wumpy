from typing import Any, Dict, Optional, Sequence, SupportsInt

from .endpoints.webhook import WebhookRequester
from .utils import MISSING, File

__all__ = ('Webhook',)


class Webhook:
    """Standalone Discord webhook authorizing using a token."""

    def __init__(self, id: int, token: str, *, wait: bool = False) -> None:
        self.id = id

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
