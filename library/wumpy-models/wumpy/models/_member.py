import dataclasses
from datetime import datetime, timezone
from typing import Optional, Tuple, Union

from discord_typings import GuildMemberAddData, GuildMemberData, UserData
from typing_extensions import Self

from ._base import Model, Snowflake
from ._flags import UserFlags
from ._permissions import Permissions
from ._user import User
from ._utils import backport_slots

__all__ = (
    'Member',
    'InteractionMember',
)


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class Member(Model):
    user: User

    nick: Optional[str]
    pending: bool

    roles: Tuple[Snowflake, ...]

    joined_at: datetime
    premium_since: Optional[datetime]
    timed_out_until: Optional[datetime]

    # Member is not a subclass of User, for memory saving reasons, but we still
    # want to fake it so that the library user can access the same attributes.
    # Without this, dealing with for example the author of messages which can
    # be either a User or Member would be very painful.

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def discriminator(self) -> int:
        return self.user.discriminator

    @property
    def public_flags(self) -> UserFlags:
        return self.user.public_flags

    @property
    def bot(self) -> bool:
        return self.user.bot

    @property
    def system(self) -> bool:
        return self.user.system

    @property
    def mention(self) -> str:
        return self.user.mention

    # Those are all user-mimicking attributes, the rest are other
    # member-specific properties.

    @property
    def timed_out(self) -> bool:
        if self.timed_out_until is None:
            return False

        return self.timed_out_until > datetime.now(timezone.utc)

    @classmethod
    def from_user(
            cls,
            user: User,
            data: Union[GuildMemberData, GuildMemberAddData],
    ) -> Self:

        premium_since = data.get('premium_since')
        if premium_since is not None:
            premium_since = datetime.fromisoformat(premium_since)

        timed_out_until = data.get('premium_since')
        if timed_out_until is not None:
            timed_out_until = datetime.fromisoformat(timed_out_until)

        return cls(
            id=user.id,
            user=user,

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data.get('roles', [])),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,
        )

    @classmethod
    def from_data(
            cls,
            data: Union[GuildMemberData, GuildMemberAddData],
            user: Optional[UserData] = None
    ) -> Self:
        if user is None:
            if 'user' not in data:
                raise ValueError('Cannot create a member without a user.')
            else:
                user = data['user']

        premium_since = data.get('premium_since')
        if premium_since is not None:
            premium_since = datetime.fromisoformat(premium_since)

        timed_out_until = data.get('premium_since')
        if timed_out_until is not None:
            timed_out_until = datetime.fromisoformat(timed_out_until)

        return cls(
            id=int(user['id']),
            user=User.from_data(user),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,
        )


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class InteractionMember(Member):
    permissions: Permissions

    @classmethod
    def from_user(cls, user: User, data: GuildMemberData) -> Self:

        premium_since = data.get('premium_since')
        if premium_since is not None:
            premium_since = datetime.fromisoformat(premium_since)

        timed_out_until = data.get('premium_since')
        if timed_out_until is not None:
            timed_out_until = datetime.fromisoformat(timed_out_until)

        return cls(
            id=user.id,
            user=user,

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,

            permissions=Permissions(int(data.get('permissions', 0))),
        )

    @classmethod
    def from_data(cls, data: GuildMemberData, user: Optional[UserData] = None) -> Self:
        if user is None and 'user' in data:
            user = data['user']
        else:
            raise ValueError('Cannot create a member without a user.')

        premium_since = data.get('premium_since')
        if premium_since is not None:
            premium_since = datetime.fromisoformat(premium_since)

        timed_out_until = data.get('premium_since')
        if timed_out_until is not None:
            timed_out_until = datetime.fromisoformat(timed_out_until)

        return cls(
            id=int(user['id']),
            user=User.from_data(user),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,

            permissions=Permissions(int(data.get('permissions', 0))),
        )
