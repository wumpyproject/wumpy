from datetime import datetime, timezone
from typing import Optional, Tuple, Union

import attrs
from discord_typings import GuildMemberAddData, GuildMemberData, UserData
from typing_extensions import Self

from .._utils import Snowflake
from ._flags import UserFlags
from ._permissions import Permissions
from ._user import RawUser

__all__ = (
    'RawMember',
    'RawInteractionMember',
)


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawMember(RawUser):
    joined_at: datetime
    roles: Tuple[Snowflake, ...]

    nick: Optional[str] = None
    pending: bool = False

    premium_since: Optional[datetime] = None
    timed_out_until: Optional[datetime] = None

    @property
    def timed_out(self) -> bool:
        if self.timed_out_until is None:
            return False

        return self.timed_out_until > datetime.now(timezone.utc)

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

            name=user['username'],
            discriminator=int(user['discriminator']),
            bot=user.get('bot', False),
            system=user.get('system', False),
            public_flags=UserFlags(user.get('public_flags', 0)),

            joined_at=datetime.fromisoformat(data['joined_at']),
            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            premium_since=premium_since,
            timed_out_until=timed_out_until,
        )


@attrs.define(eq=False, frozen=True, kw_only=True)
class RawInteractionMember(RawMember):
    permissions: Permissions = Permissions(0)

    @classmethod
    def from_data(cls, data: GuildMemberData, user: Optional[UserData] = None) -> Self:
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

            name=user['username'],
            discriminator=int(user['discriminator']),
            bot=user.get('bot', False),
            system=user.get('system', False),
            public_flags=UserFlags(user.get('public_flags', 0)),

            joined_at=datetime.fromisoformat(data['joined_at']),
            roles=tuple(Snowflake(int(s)) for s in data['roles']),

            nick=data.get('nick'),
            pending=data.get('pending', False),

            premium_since=premium_since,
            timed_out_until=timed_out_until,

            permissions=Permissions(int(data.get('permissions', 0))),
        )
