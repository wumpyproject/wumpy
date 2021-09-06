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

import datetime
from typing import Any, Dict, List, Optional, Sequence, SupportsInt

import aiohttp

from ..models import AllowedMentions
from ..rest import Route, WebhookRequester
from ..utils import MISSING, File


class InteractionRequester(WebhookRequester):
    """Requester wrapping interaction endpoints."""

    application: int

    OAUTH2_TOKEN = 'https://discord.com/api/v9/oauth2/token'

    def __init__(
        self,
        application: SupportsInt,
        *,
        secret: str = MISSING,
        token: str = MISSING,
        **kwargs
    ) -> None:
        if token is not MISSING:
            kwargs['headers'] = {'Authorization': f'Bot {token}', **kwargs.get('headers', {})}

        super().__init__(**kwargs)

        self.application = int(application)
        self.secret = secret

        self.expires_at = datetime.datetime.now()

    async def fetch_access_token(self) -> None:
        """Fetch a new access token using the Client Credentials flow."""
        data = await self.request(
            Route('POST', '/oauth2/token'),
            json={'grant_type': 'client_credentials', 'scope': 'identify'},
            auth=aiohttp.BasicAuth(str(self.application), self.secret)
        )
        expires_in = datetime.timedelta(seconds=float(data['expires_in']))
        self.expires_at = datetime.datetime.now() + expires_in

        self.headers['Authorization'] = f"Bearer {data['access_token']}"

    async def refresh(self) -> None:
        """Refresh the access token if it has expired.

        This method will not do anything if the access token has not yet
        expired, as such it is safe to call before each request.
        """
        if self.expires_at > datetime.datetime.now():
            return

        await self.fetch_access_token()

    async def fetch_global_commands(self) -> List[Any]:
        """Fetch all global commands for the application."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/applications/{application_id}/commands',
            application_id=self.application
        ))

    async def fetch_global_command(self, command: SupportsInt) -> Dict[str, Any]:
        """Fetch a specific global command."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/applications/{application_id}/commands/{command_id}}',
            application_id=self.application, command_id=int(command)
        ))

    async def delete_global_command(self, command: SupportsInt) -> None:
        """Delete a global command."""
        await self.refresh()

        await self.request(Route(
            'DELETE', '/applications/{application_id}/commands/{command_id}',
            application_id=self.application, command_id=int(command)
        ))

    async def fetch_guild_commands(self, guild: SupportsInt) -> List[Any]:
        """Fetch all commands created for a guild."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=self.application, guild_id=int(guild)
        ))

    async def fetch_guild_command(
        self,
        guild: SupportsInt,
        command: SupportsInt
    ) -> Dict[str, Any]:
        """Fetch a specific guild command."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=self.application, guild_id=int(guild), command_id=int(command)
        ))

    async def delete_guild_command(
        self,
        guild: SupportsInt,
        command: SupportsInt
    ) -> None:
        """Delete a guild specific command."""
        await self.refresh()

        await self.request(Route(
            'DELETE', '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=self.application, guild_id=int(guild), command_id=int(command)
        ))

    async def fetch_all_guild_command_permissions(self, guild: SupportsInt) -> List[Any]:
        """Fetch all permissions for all commands in a guild."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/application/{application_id}/guilds/{guild_id}/commands/permissions',
            application_id=self.application, guild_id=int(guild)
        ))

    async def fetch_guild_command_permissions(
        self,
        guild: SupportsInt,
        command: SupportsInt
    ) -> Dict[str, Any]:
        """Fetch a specific guild command's permissions."""
        await self.refresh()

        return await self.request(Route(
            'GET', '/application/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=self.application, guild_id=int(guild), command_id=int(command)
        ))

    # The following methods use the interaction token and does not require
    # further authorization (compared to the endpoints above)

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
        json = self._clean_dict(json)

        # This will cause aiohttp to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

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

        json = self._clean_dict(json)

        # Because of the usage of files here, we need to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

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
        json = self._clean_dict(json)

        # This will cause aiohttp to use multipart/form-data
        data: Dict[str, Any] = {}
        data['payload_json'] = json

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
