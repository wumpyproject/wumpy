from enum import Enum
from typing import Iterable, Optional, Sequence, SupportsInt, Tuple, Union

import attrs
from discord_typings import (
    AllowedMentionsData, AttachmentData, MessageCreateData, MessageData,
    MessageUpdateData
)
from typing_extensions import Self

from .._raw import (
    ChannelMention, Embed, RawAttachment, RawMessage, RawMessageMentions
)
from .._utils import Snowflake, _get_as_snowflake
from . import _emoji, _member, _user

__all__ = (
    'Attachment',
    'MessageMentions',
    'Message',
)


@attrs.define(eq=False)
class Attachment(RawAttachment):
    ...


@attrs.define(kw_only=True)
class MessageMentions(RawMessageMentions):
    users: Union[Tuple['_user.User', ...], Tuple['_member.Member', ...]]

    roles: Tuple[Snowflake, ...]

    @classmethod
    def from_message(
            cls,
            data: Union[MessageData, MessageCreateData, MessageUpdateData]
    ) -> Self:
        if data['mentions'] and 'member' in data['mentions'][0]:
            # Pyright doesn't understand that the type has narrowed down to
            # List[UserMentionData] with the 'member' key.
            users = tuple(_member.Member.from_data(m['member'], m) for m in data['mentions'])  # type: ignore
        else:
            users = tuple(_user.User.from_data(u) for u in data['mentions'])

        return cls(
            users=users,
            channels=tuple(
                ChannelMention.from_data(c)
                for c in data.get('mention_channels', [])
            ),
            roles=tuple(Snowflake(int(r)) for r in data['mention_roles']),
        )


@attrs.define(eq=False, kw_only=True)
class Message(RawMessage):
    author: Union[_user.User, _member.Member]

    channel_id: Snowflake
    guild_id: Optional[Snowflake] = None

    attachments: Tuple[Attachment, ...]
    reactions: Tuple['_emoji.MessageReaction', ...] = ()
    mentions: MessageMentions = MessageMentions()

    @classmethod
    def from_data(
            cls,
            data: Union[MessageData, MessageCreateData, MessageUpdateData]
    ) -> Self:
        if 'member' in data:
            author = _member.Member.from_data(data['member'], data['author'])
        else:
            author = _user.User.from_data(data['author'])

        return cls(
            id=int(data['id']),
            type=data['type'],
            author=author,

            channel_id=Snowflake(int(data['channel_id'])),
            guild_id=_get_as_snowflake(data, 'guild_id'),

            content=data['content'],
            tts=data['tts'],
            attachments=tuple(Attachment.from_data(a) for a in data['attachments']),
            embeds=tuple(Embed.from_data(e) for e in data['embeds']),
            reactions=tuple(_emoji.MessageReaction.from_data(r) for r in data.get('reactions', [])),
            mentions=MessageMentions.from_message(data),

            pinned=data['pinned'],
        )
