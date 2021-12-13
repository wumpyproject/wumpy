from typing import Any, Dict, Optional

from .base import Object
from .flags import UserFlags

__all__ = ('InteractionUser', 'BotUser', 'User')


class _BaseUser(Object):
    """The base for all user objects.

    The reason that this is seperated from User is because we don't want
    BotUser to inherit certain methods, you cannot DM yourself for example.
    """

    name: str
    discriminator: int
    avatar: Optional[str]

    public_flags: UserFlags

    bot: Optional[bool]
    system: Optional[bool]

    __slots__ = (
        'name', 'discriminator', 'avatar', 'public_flags', 'bot', 'system'
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(int(data['id']))

        self.bot = None
        self.system = None

        # We may need to update this object again, so if we seperate it
        # into another method we can call again
        self._update(data)

    def _update(self, data: Dict) -> None:
        self.name = data['username']
        self.discriminator = int(data['discriminator'])

        self.avatar = data['avatar']

        self.public_flags = UserFlags(data['public_flags'])

        self.bot = data.get('bot', self.bot)
        self.system = data.get('system', self.system)

    @property
    def mention(self) -> str:
        return f'<@{self.id}>'

    @property
    def default_avatar(self) -> int:
        # It is unneccessary to keep the default asset for each user in
        # memory, we create them when asked for.
        return self.discriminator % 5


class InteractionUser(_BaseUser):
    """User object from an interaction, this wraps no user endpoints."""
    pass


class BotUser(_BaseUser):
    """User object attached to an application; the bot application's user account."""

    bio: str
    locale: str
    mfa_enabled: bool
    verified: bool

    __slots__ = ('bio', 'locale', 'mfa_enabled', 'verified')

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

        # We may need to update this object again, so if we seperate it
        # into another method we can call again
        self._update(data)

    def _update(self, data: Dict) -> None:
        super()._update(data)

        self.bio = data['bio']
        self.locale = data['locale']

        self.mfa_enabled = data['mfa_enabled']
        self.verified = data['verified']

    @property
    def flags(self):
        return self.public_flags


class User(_BaseUser):
    """Discord User object."""

    __slots__ = ()
