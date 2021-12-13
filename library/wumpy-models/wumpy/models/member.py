from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..utils import _get_as_snowflake
from .asset import Asset
from .base import Snowflake
from .permissions import Permissions
from .user import InteractionUser

__all__ = ('InteractionMember', 'ThreadMember')


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


class ThreadMember:
    """State of a member in a thread.

    The ThreadMember object is used to indicate whether a user has joined a
    thread or not, it has details about how long a member has been in a thread.

    Attributes:
        thread_id:
            The thread the member is in, None when constructed from
            the GUILD_CREATE event.
        user_id:
            The user ID of the member, None when constructed from
            the GUILD_CREATE event.
        joined_at: Timestamp that the member joined the thread.
        flags: User thread settings (currently only used for notifications).
    """

    thread_id: Optional[Snowflake]
    user_id: Optional[Snowflake]
    joined_at: datetime
    flags: int

    __slots__ = ('thread_id', 'user_id', 'joined_at', 'flags')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.thread_id = _get_as_snowflake(data, 'id')
        self.user_id = _get_as_snowflake(data, 'user_id')

        self.joined_at = datetime.fromtimestamp(data['join_timestamp'], tz=timezone.utc)
        self.flags = data['flags']
