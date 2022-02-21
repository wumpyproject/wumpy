import dataclasses
from datetime import datetime
from typing import Optional, Tuple

from discord_typings import EmojiData
from typing_extensions import Self

from .base import Snowflake
from .user import User
from .utils import _get_as_snowflake

__all__ = ('Emoji',)


@dataclasses.dataclass(frozen=True)
class Emoji(str):

    id: Optional[Snowflake]
    name: str

    roles: Tuple[Snowflake]
    user: Optional[User]

    require_colons: bool
    managed: bool
    animated: bool
    available: bool

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
            id=_get_as_snowflake(data, 'id'),
            name=data.get('name') or '_',
            roles=tuple(Snowflake(int(s)) for s in data.get('roles', [])),
            user=user,
            require_colons=data.get('require_colons', True),
            managed=data.get('managed', False),
            animated=data.get('animated', False),
            available=data.get('available', True),
        )

    @property
    def created_at(self) -> datetime:
        """When the emoji was created extracted from the ID.

        This raises `ValueError` if there is no ID because the emoji is a
        default Discord emoji. This is so that you don't need to deal with
        None when you know that this should return a datetime.
        """
        if self.id is None:
            raise ValueError('Cannot extract a datetime from an emoji without an ID.')

        return self.id.created_at
