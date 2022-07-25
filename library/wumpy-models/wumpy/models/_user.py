import dataclasses
from typing import Union

from discord_typings import UserData, UserUpdateData
from typing_extensions import Self

from ._base import Model
from ._flags import UserFlags
from ._utils import backport_slots

__all__ = (
    'User',
    'BotUser',
)


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class User(Model):
    name: str
    discriminator: int

    bot: bool = False
    system: bool = False
    public_flags: UserFlags = UserFlags.none()

    def __str__(self) -> str:
        return f'{self.name}#{self.discriminator}'

    @property
    def mention(self) -> str:
        return f'<@{self.id}>'

    @classmethod
    def from_data(cls, data: Union[UserData, UserUpdateData]) -> Self:
        return cls(
            id=int(data['id']),
            name=data['username'],
            discriminator=int(data['discriminator']),
            bot=data.get('bot', False),
            system=data.get('system', False),
            public_flags=UserFlags(data.get('public_flags', 0))
        )


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class BotUser(Model):
    name: str
    discriminator: int

    locale: str
    mfa_enabled: bool
    verified: bool

    # As a result of these defaults, BotUser cannot be a subclass of User,
    # although that also helps with the REST API methods (cannot DM yourself).

    bot: bool = True
    system: bool = False
    public_flags: UserFlags = UserFlags.none()

    @classmethod
    def from_data(cls, data: Union[UserData, UserUpdateData]) -> Self:
        if (
            'locale' not in data
            or 'mfa_enabled' not in data
            or 'verified' not in data
        ):
            raise ValueError('Cannot create a BotUser from data without extra user fields')

        return cls(
            id=int(data['id']),
            name=data['username'],
            discriminator=int(data['discriminator']),

            locale=data['locale'],
            mfa_enabled=data['mfa_enabled'],
            verified=data['verified'],

            bot=data.get('bot', True),
            system=data.get('system', False),
            public_flags=UserFlags(data.get('public_flags', 0)),
        )
