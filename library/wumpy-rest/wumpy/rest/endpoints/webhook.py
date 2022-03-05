from typing import List, Optional, Sequence, SupportsInt, Union, overload

from discord_typings import (
    AllowedMentionsData, AttachmentData, ComponentData, EmbedData, MessageData,
    WebhookData
)
from typing_extensions import Literal

from ..route import Route
from ..utils import MISSING, dump_json
from .base import Requester, RequestFiles

__all__ = ('WebhookRequester',)


class WebhookRequester(Requester):
    """Endpoints for using and managing webhooks."""

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

        payload = {
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

    @overload
    async def execute_webhook(
        self,
        webhook: SupportsInt,
        token: str,
        *,
        wait: Literal[False] = False,
        thread: SupportsInt = MISSING,
        content: str = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[EmbedData] = MISSING,
        components: Sequence[ComponentData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: List[AllowedMentionsData] = MISSING,
    ) -> None:
        ...

    @overload
    async def execute_webhook(
        self,
        webhook: SupportsInt,
        token: str,
        *,
        wait: Literal[True],
        thread: SupportsInt = MISSING,
        content: str = MISSING,
        username: str = MISSING,
        avatar_url: str = MISSING,
        tts: bool = MISSING,
        embeds: Sequence[EmbedData] = MISSING,
        components: Sequence[ComponentData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: List[AllowedMentionsData] = MISSING,
    ) -> MessageData:
        ...

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
        embeds: Sequence[EmbedData] = MISSING,
        components: Sequence[ComponentData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: List[AllowedMentionsData] = MISSING,
    ) -> Union[MessageData, None]:
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
            files: Files to upload to Discord.
            attachments: Filename and descriptions for the files.

        Returns:
            The created message object if `wait` is specified.
        """

        if content is MISSING and embeds is MISSING and files is MISSING:
            raise TypeError("one of 'content', 'embeds' or 'files' is required")

        params = {
            'wait': wait,
            'thread_id': int(thread) if thread else MISSING,  # We cannot int() MISSING
        }

        json = {
            'content': content,
            'username': username,
            'avatar_url': str(avatar_url),
            'tts': tts,
            'embeds': embeds,
            'components': components,
            'allowed_mentions': allowed_mentions,
            'attachments': attachments
        }

        # Because of the usage of files here, we need to use multipart/form-data
        data = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        ret = await self.request(
            Route(
                'POST', '/webhooks/{webhook_id}/{webhook_token}}',
                webhook_id=int(webhook), webhook_token=token
            ),
            data=data, files=httpxfiles, params=params
        )
        if ret == '':
            return None

        return ret

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
            webhook_id=int(webhook), webhook_token=token, message_id=int(message)
        ), params={'thread_id': int(thread) if thread is not MISSING else thread})

    async def edit_webhook_message(
        self,
        webhook: SupportsInt,
        token: str,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[EmbedData]] = MISSING,
        components: Optional[Sequence[ComponentData]] = MISSING,
        allowed_mentions: Optional[AllowedMentionsData] = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: List[AttachmentData] = MISSING,
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
            files: Additional files to add to the message.
            attachments: Attachments to add, edit, or remove from the message.

        Returns:
            The updated message.
        """
        json = {
            'content': content,
            'embeds': embeds,
            'components': components,
            'allowed_mentions': allowed_mentions,
            'attachments': attachments,
        }

        # This will cause HTTPXs to use multipart/form-data
        data = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'PATCH', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
                webhook_id=int(webhook), webhook_token=token, message_id=int(message)
            ),
            data=data, files=httpxfiles
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
        """
        await self.request(Route(
            'DELETE', '/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}',
            webhook_id=int(webhook), webhook_token=token, message_id=int(message)
        ), params={'thread_id': int(thread) if thread is not MISSING else thread})
