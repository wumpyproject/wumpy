from enum import Enum
from typing import Optional

import attrs
from discord_typings import StickerData, StickerItemData
from typing_extensions import Self

from .._utils import Model, Snowflake, _get_as_snowflake
from ._user import RawUser

__all__ = (
    'RawStickerItem',
    'RawSticker',
)


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawStickerItem(Model):
    name: str
    format_type: int

    @classmethod
    def from_data(cls, data: StickerItemData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            format_type=int(data['format_type'])
        )


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawSticker(RawStickerItem):
    type: int

    tags: str
    description: Optional[str] = None

    pack_id: Optional[Snowflake] = None
    sort_value: Optional[int] = None

    available: bool = True
    guild_id: Optional[Snowflake] = None

    user: Optional[RawUser] = None

    @classmethod
    def from_data(cls, data: StickerData) -> Self:
        user = data.get('user')
        if user is not None:
            user = RawUser.from_data(user)

        return cls(
            id=int(data['id']),

            name=data['name'],
            description=data.get('description'),

            pack_id=_get_as_snowflake(data, 'pack_id'),
            sort_value=data.get('sort_value'),

            tags=data['tags'],
            type=data['type'],
            format_type=data['format_type'],

            available=data.get('available', True),
            guild_id=_get_as_snowflake(data, 'guild_id'),

            user=user
        )
