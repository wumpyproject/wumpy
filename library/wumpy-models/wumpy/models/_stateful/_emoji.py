import re
from typing import ClassVar, Optional, Tuple

import attrs
from discord_typings import EmojiData, MessageReactionData
from typing_extensions import Self

from .._raw import RawEmoji, RawMessageReaction
from .._utils import DISCORD_EPOCH, Model, Snowflake
from . import _user

__all__ = (
    'Emoji',
    'MessageReaction',
)


@attrs.define(eq=False, frozen=True)
class Emoji(RawEmoji):

    user: Optional[_user.User]

    @classmethod
    def from_data(cls, data: EmojiData) -> Self:
        user = data.get('user')
        if user is not None:
            user = _user.User.from_data(user)

        return cls(
            id=int(data['id'] or DISCORD_EPOCH << 22),
            name=data.get('name') or '_',
            roles=tuple(Snowflake(int(s)) for s in data.get('roles', [])),
            user=user,
            require_colons=data.get('require_colons', True),
            managed=data.get('managed', False),
            animated=data.get('animated', False),
            available=data.get('available', True),
        )


@attrs.define(frozen=True)
class MessageReaction(RawMessageReaction):
    emoji: Emoji

    @classmethod
    def from_data(cls, data: MessageReactionData) -> Self:
        return cls(
            count=data['count'],
            emoji=Emoji.from_data(data['emoji']),

            me=data['me'],
        )
