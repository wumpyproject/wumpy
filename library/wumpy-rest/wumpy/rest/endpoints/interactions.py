from typing import Any, Dict, Optional, Sequence, SupportsInt

from ..route import Route
from ..utils import MISSING
from .base import Requester

__all__ = ('InteractionRequester',)


class InteractionRequester(Requester):

    __slots__ = ()

    async def fetch_original_response(self, token: str) -> Dict[str, Any]:
        """Fetch the initial response to an interaction."""
        return await self.request(Route(
            'GET', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=self.application, interaction_token=token
        ))

    async def edit_original_response(
        self,
        token: str,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        file: Optional[File] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        attachments: Optional[Dict[str, Any]] = MISSING
    ) -> Dict[str, Any]:
        """Edit the original response to an interaction."""
        json: Dict[str, Any] = {
            'content': content,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else allowed_mentions,
            'attachments': attachments,
        }

        # This will cause HTTPX to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = self._clean_dict(json)

        if file is not MISSING:
            data['file'] = file

        return await self.request(Route(
            'GET', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=self.application, interaction_token=token))

    async def delete_original_response(self, token: str) -> None:
        """Delete the original response to an interaction."""
        await self.request(Route(
            'DELETE', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=self.application, interaction_token=token
        ))

    async def send_followup_message(
        self,
        token: str,
        *,
        content: str = MISSING,
        ephemeral: bool = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[Dict[str, Any]] = MISSING,
        allowed_mentions: AllowedMentions = MISSING,
        file: File = MISSING,
    ) -> Dict[str, Any]:
        """Send a followup message to an interaction."""
        if content is MISSING and embeds is MISSING and file is MISSING:
            raise TypeError("one of 'content', 'embeds' or 'file' is required")

        json: Dict[str, Any] = {
            'content': content,
            'tts': tts,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions._data if allowed_mentions else MISSING
        }
        if ephemeral is not MISSING:
            json['flags'] = 64

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = self._clean_dict(json)

        if file is not MISSING:
            data['file'] = file

        return await self.request(Route(
            'POST', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=self.application, interaction_token=token
        ))

    async def fetch_followup_message(self, token: str, message: SupportsInt) -> Dict[str, Any]:
        """Fetch a followup message previously sent."""
        return await self.request(Route(
            'GET', '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
            application_id=self.application, interaction_token=token, message_id=int(message)
        ))

    async def edit_followup_message(
        self,
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
                'PATCH', '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
                application_id_id=self.application, interaction_token=token, message_id=int(message)
            ),
            data=data
        )

    async def delete_followup_message(self, token: str, message: SupportsInt) -> None:
        """Delete a sent followup message."""
        await self.request(Route(
            'DELETE', '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
            application_id=self.application, interaction_token=token, message_id=int(message)
        ))
