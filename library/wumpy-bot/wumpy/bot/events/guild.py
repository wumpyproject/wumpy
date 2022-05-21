import dataclasses
from typing import ClassVar, FrozenSet, Optional, Sequence

from discord_typings import (
    Event, GuildBanAddData, GuildBanRemoveData, GuildDeleteData,
    GuildEmojisUpdateData, GuildMemberAddData, GuildMemberRemoveData,
    GuildMemberUpdateData, GuildRoleCreateData, GuildRoleDeleteData,
    GuildRoleUpdateData, GuildStickersUpdateData
)
from typing_extensions import Self
from wumpy.models import Emoji, Guild, Member, Role, Snowflake, Sticker, User

from ..dispatch import Event
from ..utils import _get_as_snowflake, backport_slots


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
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


@backport_slots()
@dataclasses.dataclass(frozen=True)
class MemberUpdateEvent(Event):
    guild_id: Snowflake
    member: Member
    cached: Optional[Member]

    NAME: ClassVar[str] = 'GUILD_MEMBER_UPDATE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildMemberUpdateData,
            cached: Optional[Member] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            member=Member.from_data(payload),
            cached=cached
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class RoleCreateEvent(Event):
    guild_id: Snowflake
    role: Role

    NAME: ClassVar[str] = 'GUILD_ROLE_CREATE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildRoleCreateData,
            cached: None = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role=Role.from_data(payload['role']),
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class RoleUpdateEvent(Event):
    guild_id: Snowflake
    role: Role
    cached: Optional[Role]

    NAME: ClassVar[str] = 'GUILD_ROLE_UPDATE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildRoleCreateData,
            cached: Optional[Role] = None
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role=Role.from_data(payload['role']),
            cached=cached
        )


@backport_slots()
@dataclasses.dataclass(frozen=True)
class RoleDeleteEvent(Event):
    guild_id: Snowflake
    role_id: Snowflake
    cached: Optional[Role]

    NAME: ClassVar[str] = 'GUILD_ROLE_DELETE'

    @classmethod
    async def from_payload(
            cls,
            payload: GuildRoleDeleteData,
            cached: Optional[Role] = None,
    ) -> Self:
        return cls(
            guild_id=Snowflake(payload['guild_id']),
            role_id=Snowflake(payload['role_id']),
            cached=cached
        )
