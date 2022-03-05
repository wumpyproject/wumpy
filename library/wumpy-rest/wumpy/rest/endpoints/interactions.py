from typing import Optional, Sequence, SupportsInt, overload

from discord_typings import (
    AllowedMentionsData, AttachmentData, AutocompleteOptionData, ComponentData,
    EmbedData, MessageData, PartialAttachmentData
)
from typing_extensions import Literal

from ..route import Route
from ..utils import MISSING, dump_json
from .base import Requester, RequestFiles

__all__ = ('InteractionRequester',)


class InteractionRequester(Requester):
    """Endpoints for responding to interactions."""

    __slots__ = ()

    @overload
    async def create_interaction_response(
        self,
        application: SupportsInt,
        token: str,
        type: Literal[1, 5, 6]
    ) -> None:
        ...

    @overload
    async def create_interaction_response(
        self,
        application: SupportsInt,
        token: str,
        type: Literal[8],
        *,
        choices: Sequence[AutocompleteOptionData]
    ) -> None:
        ...

    @overload
    async def create_interaction_response(
        self,
        application: SupportsInt,
        token: str,
        type: Literal[9],
        *,
        custom_id: str,
        title: str,
        components: Sequence[ComponentData]
    ) -> None:
        ...

    @overload
    async def create_interaction_response(
        self,
        application: SupportsInt,
        token: str,
        type: Literal[4, 7],
        *,
        content: str = MISSING,
        tts: bool = MISSING,
        flags: int = MISSING,
        embeds: Sequence[EmbedData] = MISSING,
        components: Sequence[ComponentData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Sequence[PartialAttachmentData] = MISSING,
    ) -> None:
        ...

    async def create_interaction_response(
        self,
        application: SupportsInt,
        token: str,
        type: int,
        *,
        choices: Sequence[AutocompleteOptionData] = MISSING,
        custom_id: str = MISSING,
        title: str = MISSING,
        components: Sequence[ComponentData] = MISSING,
        content: str = MISSING,
        tts: bool = MISSING,
        flags: int = MISSING,
        embeds: Sequence[EmbedData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Sequence[PartialAttachmentData] = MISSING,
    ) -> None:
        """Create the original response to an interaction.

        This is for use when responding to interactions through the gateway.
        Depending on the overload and type of interaction used, see the
        different set of parameters you can pass.

        Parameters:
            choices: The suggested autocomplete choices.

        Parameters:
            custom_id: The custom ID of the modal.
            title: The displayed title of the modal.
            components: Text input components for the modal.

        Parameters:
            content: The content for the message.
            tts: Whether this should be a TTS message.
            flags:
                Flags to apply for the followup message. Set this to 64 to
                create an ephemeral message.
            embeds: Embeds to display for this message.
            components: Message components to attach to the message.
            allowed_mentions:
                A special allowed mentions object telling Discord what mentions
                to parse and ping in the client.
            files: Files to upload to Discord.
            attachments: Filename and descriptions for the files.
        """
        json = {
            'type': type,
            'data': {
                'choices': choices,

                'custom_id': custom_id,
                'title': title,
                'components': components,

                'content': content,
                'tts': tts,
                'flags': flags,
                'embeds': embeds,
                # 'components': components,
                'allowed_mentions': allowed_mentions,
                'attachments': attachments
            }
        }

        data = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'POST', '/webhooks/{application_id}/{interaction_token}}/callback',
                application_id=int(application), interaction_token=token
            ),
            data=data, files=httpxfiles
        )

    async def fetch_original_response(
        self,
        application: SupportsInt,
        token: str,
    ) -> MessageData:
        """Fetch the original interaction response.

        Parameters:
            application: The ID of the application.
            token: The token of the interaction.

        Returns:
            The message that was created from the interaction response.
        """
        return await self.request(Route(
            'GET', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=int(application), interaction_token=int(token)
        ))

    async def edit_original_response(
        self,
        application: SupportsInt,
        token: str,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[EmbedData]] = MISSING,
        components: Optional[Sequence[ComponentData]] = MISSING,
        allowed_mentions: Optional[AllowedMentionsData] = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Sequence[AttachmentData] = MISSING,
    ) -> MessageData:
        """Edit the original response for an interaction.

        Parameters:
            application: The ID of the application.
            token: The token of the interaction.
            content: The new content of the message.
            embeds: The new list of embeds to display.
            components: The new overriden message components to attach.
            allowed_mentions:
                Mentions allowed to ping in the client for the (new) content.
                This does not have much of a use.
            files: Additional files to add to the message.
            attachments: Attachments to add, edit, or remove from the message.

        Returns:
            The updated interaction response.
        """
        json = {
            'content': content,
            'embeds': embeds,
            'components': components,
            'allowed_mentions': allowed_mentions,
            'attachments': attachments,
        }

        # This will cause HTTPx to use multipart/form-data
        data = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'PATCH',
                '/webhooks/{application_id}/{interaction_token}/messages/@original',
                application_id=int(application), interaction_token=token
            ),
            data=data, files=httpxfiles
        )

    async def delete_original_response(
        self,
        application: SupportsInt,
        token: str,
    ) -> None:
        """Delete the original response sent to an interaction.

        Parameters:
            application: The ID of the application.
            token: The token for the interaction.
        """
        await self.request(Route(
            'DELETE', '/webhooks/{application_id}/{interaction_token}/messages/@original',
            application_id=int(application), interaction_token=token
        ))

    async def send_followup_message(
        self,
        application: SupportsInt,
        token: str,
        *,
        content: str = MISSING,
        tts: bool = MISSING,
        flags: int = MISSING,
        embeds: Sequence[EmbedData] = MISSING,
        components: Sequence[ComponentData] = MISSING,
        allowed_mentions: AllowedMentionsData = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Sequence[AllowedMentionsData] = MISSING,
    ) -> MessageData:
        """Send a followup message to an interaction.

        Parameters:
            application: The ID of the application.
            token: The token for the interaction.
            content: The content for the message.
            tts: Whether this should be a TTS message.
            flags:
                Flags to apply for the followup message. Set this to 64 to
                create an ephemeral message.
            embeds: Embeds to display for this message.
            components: Message components to attach to the message.
            allowed_mentions:
                A special allowed mentions object telling Discord what mentions
                to parse and ping in the client.
            files: Files to upload to Discord.
            attachments: Filename and descriptions for the files.

        Returns:
            The created followup message data.
        """

        if content is MISSING and embeds is MISSING and files is MISSING:
            raise TypeError("one of 'content', 'embeds' or 'files' is required")

        json = {
            'content': content,
            'tts': tts,
            'flags': flags,
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

        return await self.request(
            Route(
                'POST', '/webhooks/{application_id}/{interaction_token}}',
                application_id=int(application), interaction_token=token
            ),
            data=data, files=httpxfiles
        )

    async def fetch_followup_message(
        self,
        application: SupportsInt,
        token: str,
        message: SupportsInt,
    ) -> MessageData:
        """Fetch a follow up message to the interaction.

        This does not support ephemeral followups, you cannot fetch those.

        Parameters:
            application: The ID of the application.
            token: The token of the interaction.
            message: The ID of the followup message to fetch.

        Returns:
            The message object returned by Discord.
        """
        return await self.request(Route(
            'GET', '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
            application_id=int(application), interaction_token=int(token),
            message_id=int(message)
        ))

    async def edit_followup_message(
        self,
        application: SupportsInt,
        token: str,
        message: SupportsInt,
        *,
        content: Optional[str] = MISSING,
        embeds: Optional[Sequence[EmbedData]] = MISSING,
        components: Optional[Sequence[ComponentData]] = MISSING,
        allowed_mentions: Optional[AllowedMentionsData] = MISSING,
        files: Optional[RequestFiles] = None,
        attachments: Sequence[AttachmentData] = MISSING,
    ) -> MessageData:
        """Edit a followup message for the interaction.

        Parameters:
            application: The ID of the application.
            token: The token of the interaction.
            message: The ID of the followup message to edit.
            content: The new content of the message.
            embeds: The new list of embeds to display.
            components: The new overriden message components to attach.
            allowed_mentions:
                Mentions allowed to ping in the client for the (new) content.
                This does not have much of a use.
            files: Additional files to add to the message.
            attachments: Attachments to add, edit, or remove from the message.

        Returns:
            The updated followup message.
        """
        json = {
            'content': content,
            'embeds': embeds,
            'components': components,
            'allowed_mentions': allowed_mentions,
            'attachments': attachments,
        }

        # This will cause HTTPx to use multipart/form-data
        data = {'payload_json': dump_json(self._clean_dict(json))}

        if files is not None:
            httpxfiles = tuple((f'files[{i}]', f) for i, f in enumerate(files))
        else:
            httpxfiles = None

        return await self.request(
            Route(
                'PATCH',
                '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
                application_id=int(application), interaction_token=token,
                message_id=int(message)
            ),
            data=data, files=httpxfiles
        )

    async def delete_followup_message(
        self,
        application: SupportsInt,
        token: str,
        message: SupportsInt,
    ) -> None:
        """Delete a followup message sent to an interaction.

        This cannot delete ephemeral followups.

        Parameters:
            application: The ID of the application.
            token: The token for the interaction.
            message: The ID of the followup to delete.
        """
        await self.request(Route(
            'DELETE', '/webhooks/{application_id}/{interaction_token}/messages/{message_id}',
            application_id=int(application), interaction_token=token, message_id=int(message)
        ))
