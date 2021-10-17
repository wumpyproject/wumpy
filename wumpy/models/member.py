from datetime import datetime
from typing import Any, Dict, List, Optional

from .asset import Asset
from .base import Snowflake
from .permissions import Permissions
from .user import InteractionUser

__all__ = ('InteractionMember',)


class InteractionMember(InteractionUser):
    """Uncached member received from an interaction."""

    nick: Optional[str]
    roles: List[Snowflake]
    guild_avatar: Optional[Asset]

    joined_at: datetime
    premium_since: Optional[datetime]
    pending: bool

    permissions: Permissions

    __slots__ = (
        'nick', 'roles', 'guild_avatar', 'joined_at', 'premium_since',
        'pending', 'permissions'
    )

    def __init__(self, rest, guild_id: int, data: Dict[str, Any]) -> None:
        super().__init__(rest, data['user'])

        self.nick = data.get('nick')
        self.roles = [Snowflake(int(id_)) for id_ in data['roles']]
        avatar = data.get('avatar')
        if avatar:
            self.guild_avatar = Asset(
                rest,
                f'guilds/{guild_id}/users/{self.id}/avatars/{avatar}'
            )
        else:
            self.guild_avatar = None

        self.joined_at = data['joined_at']
        self.premium_since = data.get('premium_since')
        self.pending = data.get('pending', False)

        self.permissions = Permissions(data['permissions'])
