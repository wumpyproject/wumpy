from enum import Enum
from typing import Optional

import attrs
from discord_typings import StickerData, StickerItemData
from typing_extensions import Self

from ._user import User
from ._utils import Model, Snowflake, _get_as_snowflake

__all__ = (
    'StickerType',
    'StickerFormatType',
    'StickerItem',
    'Sticker',
)


class StickerType(Enum):
    standard = 1
    guild = 2


class StickerFormatType(Enum):
    png = 1
    apng = 2
    lottie = 3


@attrs.define(eq=False, kw_only=True)
class StickerItem(Model):
    name: str
    format_type: StickerFormatType

    @classmethod
    def from_data(cls, data: StickerItemData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            format_type=StickerFormatType(int(data['format_type']))
        )


@attrs.define(eq=False, kw_only=True)
class Sticker(StickerItem):
    type: StickerType

    tags: str
    description: Optional[str] = None

    pack_id: Optional[Snowflake] = None
    sort_value: Optional[int] = None

    available: bool = True
    guild_id: Optional[Snowflake] = None

    user: Optional[User] = None

    @classmethod
    def from_data(cls, data: StickerData) -> Self:
        user = data.get('user')
        if user is not None:
            user = User.from_data(user)

        return cls(
            id=int(data['id']),

            name=data['name'],
            description=data.get('description'),

            pack_id=_get_as_snowflake(data, 'pack_id'),
            sort_value=data.get('sort_value'),

            tags=data['tags'],
            type=StickerType(data['type']),
            format_type=StickerFormatType(data['format_type']),

            available=data.get('available', True),
            guild_id=_get_as_snowflake(data, 'guild_id'),

            user=user
        )
