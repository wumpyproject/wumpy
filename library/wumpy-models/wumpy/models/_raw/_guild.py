from typing import List, Optional, Set, Union

import attrs
from discord_typings import GuildCreateData, GuildData, GuildUpdateData
from typing_extensions import Literal, Self

from .._utils import Model, Snowflake, _get_as_snowflake

__all__ = (
    'RawGuild',
)


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawGuild(Model):
    name: str
    owner_id: Snowflake

    icon: Optional[str]
    splash: Optional[str]
    discovery_splash: Optional[str]

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

            icon=data.get('icon'),
            splash=data.get('splash'),
            discovery_splash=data.get('discovery_splash'),

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
