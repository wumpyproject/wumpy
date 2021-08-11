from typing import TYPE_CHECKING, Dict, Optional

from .asset import Asset
from .base import Object
from .flags import UserFlags

if TYPE_CHECKING:
    from ..state import ApplicationState

__all__ = ('User', 'ApplicationUser')


class User(Object):
    """Discord User object."""

    _state: 'ApplicationState'

    username: str
    discriminator: int
    avatar: Optional[Asset]

    public_flags: UserFlags

    bot: Optional[bool]
    system: Optional[bool]

    __slots__ = (
        '_state', 'username', 'discriminator',
        'avatar', 'public_flags', 'bot', 'system'
    )

    def __init__(self, state: 'ApplicationState', data: Dict) -> None:
        super().__init__(int(data['id']))
        self._state = state

        self.username = data['username']
        self.discriminator = int(data['discriminator'])

        avatar = data['avatar']
        self.avatar = Asset(self._state, f'avatars/{self.id}/{avatar}') if avatar else None

        self.public_flags = UserFlags(data.get('public_flags', 0))

        self.bot = data.get('bot')
        self.system = data.get('system')

    @property
    def mention(self):
        return f'<@{self.id}>'

    @property
    def default_avatar(self):
        # It is unneccessary to keep the default asset for each user in
        # memory, we create them when asked for.
        return Asset(self._state, f'embed/avatars/{self.discriminator % 5}')
