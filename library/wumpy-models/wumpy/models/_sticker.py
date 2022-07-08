import dataclasses
from enum import Enum
from typing import Optional

from discord_typings import StickerData, StickerItemData
from typing_extensions import Self

from ._base import Model, Snowflake
from ._user import User
from ._utils import _get_as_snowflake, backport_slots

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


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
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


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class Sticker(StickerItem):
    description: Optional[str]

    pack_id: Optional[Snowflake]
    sort_value: Optional[int]

    tags: str
    type: StickerType

    available: bool
    guild_id: Optional[Snowflake]

    user: Optional[User]

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
