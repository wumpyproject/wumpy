from typing import Optional

import attrs
from discord_typings import StickerData
from typing_extensions import Self

from .._raw import RawSticker, RawStickerItem, StickerFormatType, StickerType
from .._utils import _get_as_snowflake
from . import _user

__all__ = (
    'StickerItem',
    'Sticker',
)


@attrs.define(eq=False, kw_only=True)
class StickerItem(RawStickerItem):
    ...


@attrs.define(eq=False, kw_only=True)
class Sticker(RawSticker, StickerItem):
    type: StickerType

    user: Optional['_user.User']

    @classmethod
    def from_data(cls, data: StickerData) -> Self:
        user = data.get('user')
        if user is not None:
            user = _user.User.from_data(user)

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
