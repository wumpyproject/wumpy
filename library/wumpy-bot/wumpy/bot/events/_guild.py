from typing import ClassVar, FrozenSet, Optional, Sequence

import attrs
from discord_typings import (
    GuildBanAddData, GuildBanRemoveData, GuildDeleteData,
    GuildEmojisUpdateData, GuildMemberAddData, GuildMemberRemoveData,
    GuildMemberUpdateData, GuildRoleCreateData, GuildRoleDeleteData,
    GuildStickersUpdateData
)
from typing_extensions import Self
from wumpy.models import Emoji, Guild, Member, Role, Snowflake, Sticker, User

from .._dispatch import Event

__all__ = (
    'GuildDeleteEvent',
    'BanAddEvent',
    'BanRemoveEvent',
    'GuildEmojisUpdateEvent',
    'GuildStickersUpdateEvent',
    'MemberJoinEvent',
    'MemberRemoveEvent',
    'MemberUpdateEvent',
    'RoleCreateEvent',
    'RoleUpdateEvent',
    'RoleDeleteEvent',
)


@attrs.define(kw_only=True)
class GuildDeleteEvent(Event):
    unavailable: Optional[bool]

    guild: Optional[Guild]

    NAME: ClassVar[str] = 'GUILD_DELETE'

    @property
    def removed(self) -> bool:
        return self.unavailable is None

    @classmethod
    async def from_payload(
            cls,
            payload: GuildDeleteData,
            cached: Optional[Guild] = None
    ) -> Self:
        return cls(unavailable=payload.get('unavailable'), guild=cached)


@attrs.define(kw_only=True)
class BanAddEvent(Event):
    guild_id: Snowflake

    member: Optional[Member]
    user: User

    NAME: ClassVar[str] = 'GUILD_BAN_ADD'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildBanAddData,
            cached: Optional[Member] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            member=cached,
            user=User.from_data(payload['user']),
        )


@attrs.define(kw_only=True)
class BanRemoveEvent(Event):
    guild_id: Snowflake
    user: User

    NAME: ClassVar[str] = 'GUILD_BAN_REMOVE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildBanRemoveData,
            cached: None = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            user=User.from_data(payload['user']),
        )


@attrs.define(kw_only=True)
class GuildEmojisUpdateEvent(Event):
    guild_id: Snowflake

    removed: Optional[FrozenSet[Emoji]]
    emojis: FrozenSet[Emoji]

    NAME: ClassVar[str] = 'GUILD_EMOJIS_UPDATE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildEmojisUpdateData,
            cached: Optional[Sequence[Emoji]] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),

            removed=frozenset(cached) if cached is not None else None,
            emojis=frozenset([Emoji.from_data(data) for data in payload['emojis']])
        )


@attrs.define(kw_only=True)
class GuildStickersUpdateEvent(Event):
    guild_id: Snowflake

    removed: Optional[FrozenSet[Sticker]]
    stickers: FrozenSet[Sticker]

    NAME: ClassVar[str] = 'GUILD_STICKERS_UPDATE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildStickersUpdateData,
            cached: Optional[Sequence[Sticker]] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),

            removed=frozenset(cached) if cached is not None else None,
            stickers=frozenset([Sticker.from_data(data) for data in payload['stickers']])
        )


@attrs.define(kw_only=True)
class MemberJoinEvent(Event):
    guild_id: Snowflake
    member: Member

    NAME: ClassVar[str] = 'GUILD_MEMBER_ADD'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildMemberAddData,
            cached: None = None
    ) -> Self:
        return cls(
            member=Member.from_data(payload),
            guild_id=Snowflake(payload['guild_id'])
        )


@attrs.define(kw_only=True)
class MemberRemoveEvent(Event):
    guild_id: Snowflake
    user: User

    NAME: ClassVar[str] = 'GUILD_MEMBER_REMOVE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildMemberRemoveData,
            cached: None = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            user=User.from_data(payload['user'])
        )


@attrs.define(kw_only=True)
class MemberUpdateEvent(Event):
    guild_id: Snowflake
    member: Member
    cached: Optional[Member]

    NAME: ClassVar[str] = 'GUILD_MEMBER_UPDATE'

    @classmethod
    def from_payload(
            cls,
            payload: GuildMemberUpdateData,
            cached: Optional[Member] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            member=Member.from_data(payload),
            cached=cached
        )


@attrs.define(kw_only=True)
class RoleCreateEvent(Event):
    guild_id: Snowflake
    role: Role

    NAME: ClassVar[str] = 'GUILD_ROLE_CREATE'

    @classmethod
    def from_payload(
            cls,
            payload: GuildRoleCreateData,
            cached: None = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role=Role.from_data(payload['role']),
        )


@attrs.define(kw_only=True)
class RoleUpdateEvent(Event):
    guild_id: Snowflake
    role: Role
    cached: Optional[Role]

    NAME: ClassVar[str] = 'GUILD_ROLE_UPDATE'

    @classmethod
    def from_payload(
            cls,
            payload: GuildRoleCreateData,
            cached: Optional[Role] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role=Role.from_data(payload['role']),
            cached=cached
        )


@attrs.define(kw_only=True)
class RoleDeleteEvent(Event):
    guild_id: Snowflake
    role_id: Snowflake
    cached: Optional[Role]

    NAME: ClassVar[str] = 'GUILD_ROLE_DELETE'

    @classmethod
    def from_payload(
            cls,
            payload: GuildRoleDeleteData,
            cached: Optional[Role] = None,
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role_id=Snowflake(payload['role_id']),
            cached=cached
        )
