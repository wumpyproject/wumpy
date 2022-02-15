import dataclasses

from discord_typings import UserData
from typing_extensions import Self

from .base import Model
from .flags import UserFlags

__all__ = ('BotUser', 'User')


@dataclasses.dataclass(frozen=True, eq=False)
class User(Model):
    name: str
    discriminator: int
    public_flags: UserFlags

    bot: bool
    system: bool

    def __str__(self) -> str:
        return f'{self.name}#{self.discriminator}'

    @property
    def mention(self) -> str:
        return f'<@{self.id}>'

    @classmethod
    def from_data(cls, data: UserData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['username'],
            discriminator=int(data['discriminator']),
            bot=data.get('bot', False),
            system=data.get('system', False),
            public_flags=UserFlags(data.get('public_flags', 0))
        )


@dataclasses.dataclass(frozen=True, eq=False)
class BotUser(User):
    locale: str
    mfa_enabled: bool
    verified: bool

    @classmethod
    def from_data(cls, data: UserData) -> Self:
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
            public_flags=UserFlags(data.get('public_flags', 0)),
            bot=data.get('bot', False),
            system=data.get('system', False),

            locale=data['locale'],
            mfa_enabled=data['mfa_enabled'],
            verified=data['verified'],
        )
