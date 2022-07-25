from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Set, Union

from discord_typings import GuildCreateData, GuildData, GuildUpdateData
from typing_extensions import Literal, Self

from ._asset import Asset
from ._base import Model, Snowflake
from ._utils import _get_as_snowflake

__all__ = (
    'Guild',
)


def _get_as_asset(data: Optional[Mapping[str, Any]], key: str) -> Optional[Asset]:
    if data is None:
        return None

    value: Optional[str] = data.get(key)
    return Asset.from_path(value) if value is not None else None


@dataclass(frozen=True, eq=False)
class Guild(Model):
    name: str
    owner_id: Snowflake

    icon: Optional[Asset]
    splash: Optional[Asset]
    discovery_splash: Optional[Asset]

    features: Set[str]

    afk_timeout: int
    afk_channel_id: Optional[Snowflake]

    verification_level: Literal[0, 1, 2, 3, 4]
    default_notifications: Literal[0, 1]
    explicit_content_filter: Literal[0, 1, 2]
    mfa_level: Literal[0, 1]
    premium_tier: Literal[0, 1, 2, 3]
    nsfw_level: Literal[0, 1, 2, 3]

    # This is an exception to the immutabily rule, as we want to keep the list
    # of these IDs up-to-date without needing to somehow re-create the entire
    # guild object each time.

    roles: List[Snowflake]
    emojis: List[Snowflake]
    members: List[Snowflake]
    channels: List[Snowflake]

    @classmethod
    def from_data(cls, data: Union[GuildData, GuildCreateData, GuildUpdateData]) -> Self:
        return cls(
            id=int(data['id']),
            name=data['name'],
            owner_id=Snowflake(int(data['owner_id'])),

            icon=_get_as_asset(data, 'icon'),
            splash=_get_as_asset(data, 'splash'),
            discovery_splash=_get_as_asset(data, 'discovery_splash'),

            features=set(data['features']),


            afk_timeout=data['afk_timeout'],
            afk_channel_id=_get_as_snowflake(data, 'afk_channel_id'),

            verification_level=data['verification_level'],
            default_notifications=data['default_message_notifications'],
            explicit_content_filter=data['explicit_content_filter'],
            mfa_level=data['mfa_level'],
            premium_tier=data['premium_tier'],
            nsfw_level=data['nsfw_level'],

            roles=[Snowflake(int(item['id'])) for item in data['roles']],
            emojis=[
                Snowflake(int(item['id'])) for item in data['emojis']
                if item['id'] is not None
            ],
            channels=[Snowflake(int(item['id'])) for item in data.get('channels', [])],
            members=[]
        )
