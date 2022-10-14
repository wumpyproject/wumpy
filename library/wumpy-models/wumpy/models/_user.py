import attrs
from discord_typings import UserData
from typing_extensions import Self

from ._flags import UserFlags
from ._utils import Model

__all__ = (
    'User',
    'BotUser',
)


@attrs.define(eq=False, kw_only=True)
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
    def from_data(cls, data: UserData) -> Self:
        return cls(
            id=int(data['id']),
            name=data['username'],
            discriminator=int(data['discriminator']),
            bot=data.get('bot', False),
            system=data.get('system', False),
            public_flags=UserFlags(data.get('public_flags', 0))
        )


@attrs.define(eq=False, kw_only=True)
class BotUser(User):
    bot: bool = True  # Update default

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

            locale=data['locale'],
            mfa_enabled=data['mfa_enabled'],
            verified=data['verified'],

            bot=data.get('bot', True),
            system=data.get('system', False),
            public_flags=UserFlags(data.get('public_flags', 0)),
        )
