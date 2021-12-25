from typing import Any, Dict, Optional, Sequence, SupportsInt, overload

from discord_typings import AllowedMentionsData, MessageData, WebhookData

from ..route import Route
from ..utils import MISSING, File
from .base import Requester


class WebhookRequester(Requester):
    """Requester subclass for use with a Requester."""

    __slots__ = ()

    async def fetch_webhook(self, webhook: SupportsInt, token: str) -> WebhookData:
        """Fetch a specific webhook by its ID.

        The `token` parameter is optional, but requires that the requester is
        initialized with the `Authorization` header containing the bot token.

        Passing the token also results in the `user` field to be returned in
        the payload - this is not the case otherwise.

        Parameters:
            webhook: The ID of the webhook to fetch.
            token: The token of the webhook being fetched.

        Returns:
            The webhook object returned from Discord.
        """
        if token is MISSING:
            return await self.request(Route(
                'GET', '/webhooks/{webhook_id}', webhook_id=int(webhook)
            ))

        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ))

    @overload
    async def edit_webhook(
        self,
        webhook: SupportsInt,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
        channel: SupportsInt = MISSING
    ) -> WebhookData:
        ...

    @overload
    async def edit_webhook(
        self,
        webhook: SupportsInt,
        token: str,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
    ) -> WebhookData:
        ...

    async def edit_webhook(
        self,
        webhook: SupportsInt,
        token: str = MISSING,
        *,
        name: str = MISSING,
        avatar: str = MISSING,
        channel: SupportsInt = MISSING
    ) -> WebhookData:
        """Edit values of a webhook.

        If used without the `token`, this requires the requester to be
        initialized with the `Authorization` header and the bot has to have the
        `MANAGE_WEBHOOKS` permission.

        Parameters:
            webhook: The ID of the webhook to edit.
            token: The token of the webhook being edited.
            name: The new name of the webhook.
            avatar: Image data for the webhook's new avatar.
            channel: The ID of the channel this webhook should be moved to.

        Returns:
            The updated webhook object.
        """
        if name is MISSING and avatar is MISSING and channel is MISSING:
            raise TypeError("at least one of 'username', 'avatar' or 'channel' is required")
        elif token is MISSING and channel is not MISSING:
            raise TypeError("cannot specify 'channel' when using webhook token authorization")

        payload: Dict[str, Any] = {
            'name': name,
            'avatar': avatar,
            'channel': int(channel) if channel is not MISSING else channel
        }

        if token is MISSING:
            return await self.request(
                Route('PATCH', '/webhooks/{webhook_id}', webhook_id=int(webhook)),
                json=payload
            )

        return await self.request(Route(
            'PATCH', '/webhooks/{webhook_id}/{webhook_token}',
            webhook_id=int(webhook), webhook_token=token
        ), json=payload)

    async def delete_webhook(self, webhook: SupportsInt, token: str) -> None:
        """Delete a webhook permanently.

        If used without the `token`, this requires the requester to be
        initialized with the `Authorization` header and the bot has to have the
        `MANAGE_WEBHOOKS` permission.

        Parameters:
            webhook: The ID of the webhook to delete.
            token: The token for the webhook being deleted.
        """
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
        allowed_mentions: AllowedMentionsData = MISSING,
        file: File = MISSING,
    ) -> MessageData:
        """Execute a webhook and send a message in the channel it's setup in.

        Unlike many other endpoints, the token is always required to call this
        endpoint.

        Parameters:
            webhook: The ID of the webhook to execute.
            token: The token for the webhook being executed.
            wait: Whether to wait and confirm that the message was created.
            thread: The thread to post the message in.
            content: The content for the message.
            username: The username to display for the message in the client.
            avatar_url: URL to use for the avatar for the message.
            tts: Whether this should be a TTS message.
            embeds: Embeds to display for this message.
            allowed_mentions:
                A special allowed mentions object telling Discord what mentions
                to parse and ping in the client.
            file: Special file object to send as an attachment.
        """

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
            'allowed_mentions': allowed_mentions
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
        message: SupportsInt,
        *,
        thread: SupportsInt = MISSING
    ) -> MessageData:
        """Fetch a webhook's previously sent message.

        If the message was sent in a thread then `thread` is required.

        Parameters:
            webhook: The ID of the webhook that sent the message.
            token: The token of the webhook.
            message: The ID of the message to fetch.
            thread:
                The thread that the message was sent in. Only necessary if it
                was sent in a thread.

        Returns:
            The message object returned by Discord.
        """
        return await self.request(Route(
            'GET', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
        ), params={'thread_id': int(thread) if thread is not MISSING else thread})

    async def edit_webhook_message(
        self,
        webhook: SupportsInt,
        token: str,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[Dict[str, Any]]] = MISSING,
        allowed_mentions: Optional[AllowedMentionsData] = MISSING,
        file: Optional[File] = MISSING
    ) -> MessageData:
        """Edit a message the webhook sent previously.

        Parameters:
            webhook: The ID of the webhook that sent the message.
            token: The token of the webhook.
            message: The ID of the message to edit.
            content: The new content of the message.
            embeds: The new list of embeds to display.
            allowed_mentions:
                Mentions allowed to ping in the client for the (new) content.
                This does not have much of a use.
            file: Another file to upload with the message.

        Returns:
            The updated message.
        """
        json: Dict[str, Any] = {
            'content': content,
            'embeds': embeds,
            'allowed_mentions': allowed_mentions,
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
        message: SupportsInt,
        *,
        thread: SupportsInt = MISSING
    ) -> None:
        """Delete a webhook's previously sent message.

        Parameters:
            webhook: The webhook that sent the message.
            token: The token of the webhook.
            message: The ID of the message to delete.
            thread:
                The thread the message was sent in, only required if the
                message was originally sent in a thread.

        Returns:
            Nothing - on failure raises an exception.
        """
        await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=int(token), message_id=int(message)
        ), params={'thread_id': int(thread) if thread is not MISSING else thread})
