import dataclasses
import re
from typing import Optional, Tuple

from discord_typings import EmojiData, MessageReactionData
from typing_extensions import Self

from .base import DISCORD_EPOCH, Model, Snowflake
from .user import User

__all__ = ['Emoji', 'MessageReaction']


@dataclasses.dataclass(frozen=True, eq=False)
class Emoji(Model):

    name: str

    roles: Tuple[Snowflake, ...]
    user: Optional[User]

    require_colons: bool
    managed: bool
    animated: bool
    available: bool

    REGEX = re.compile(r'<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')

    __slots__ = (
        'id', 'name', 'animated', 'roles', 'user', 'require_colons', 'managed',
        'animated', 'available',
    )

    @classmethod
    def from_data(cls, data: EmojiData) -> Self:
        user = data.get('user')
        if user is not None:
            user = User.from_data(user)

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

    @classmethod
    def from_string(cls, value: str) -> Self:
        match = cls.REGEX.match(value)
        if match:
            return cls(
                id=int(match.group('id')),
                name=match.group('name'),
                roles=(),
                user=None,

                require_colons=True,
                managed=False,
                animated=bool(match.group('animated')),
                available=True
            )

        # The regex didn't match, we'll just have to assume the user passed a
        # built-in unicode emoji
        return cls(
            id=DISCORD_EPOCH << 22,
            name=value,
            roles=(),
            user=None,

            require_colons=False,
            managed=False,
            animated=False,
            available=True
        )


@dataclasses.dataclass(frozen=True)
class MessageReaction:
    count: int
    me: bool
    emoji: Emoji

    __slots__ = ('count', 'me', 'emoji')

    @classmethod
    def from_data(cls, data: MessageReactionData) -> Self:
        return cls(
            count=data['count'],
            me=data['me'],
            emoji=Emoji.from_data(data['emoji'])
        )
