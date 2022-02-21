import dataclasses
from datetime import datetime, timezone
from typing import Optional, Tuple

from discord_typings import GuildMemberData, UserData
from typing_extensions import Self

from .base import Snowflake
from .flags import UserFlags
from .permissions import Permissions
from .user import User

__all__ = ('Member', 'InteractionMember')


@dataclasses.dataclass(frozen=True, eq=False)
class Member(User):
    nick: Optional[str]
    pending: bool

    roles: Tuple[Snowflake, ...]

    joined_at: datetime
    premium_since: Optional[datetime]
    timed_out_until: Optional[datetime]

    @classmethod
    def from_data(cls, user: Optional[UserData], data: GuildMemberData) -> Self:
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
            name=user['username'],
            discriminator=int(user['discriminator']),
            bot=user.get('bot', False),
            system=user.get('system', False),
            public_flags=UserFlags(user.get('public_flags', 0)),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,
        )

    @property
    def timed_out(self) -> bool:
        if self.timed_out_until is None:
            return False

        return self.timed_out_until > datetime.now(timezone.utc)


@dataclasses.dataclass(frozen=True, eq=False)
class InteractionMember(Member):
    permissions: Permissions

    @classmethod
    def from_data(cls, user: Optional[UserData], data: GuildMemberData) -> Self:
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
            name=user['username'],
            discriminator=int(user['discriminator']),
            bot=user.get('bot', False),
            system=user.get('system', False),
            public_flags=UserFlags(user.get('public_flags', 0)),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            joined_at=datetime.fromisoformat(data['joined_at']),
            premium_since=premium_since,
            timed_out_until=timed_out_until,

            permissions=Permissions(int(data.get('permissions', 0))),
        )
