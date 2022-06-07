import dataclasses
from datetime import datetime, timezone
from typing import Optional

from discord_typings import InviteData
from typing_extensions import Self

from .channels import PartialChannel
from .user import User
from .utils import backport_slots

__all__ = ('Invite',)


@backport_slots()
@dataclasses.dataclass(frozen=True, eq=False)
class Invite:
    """Representation of a Discord invite."""

    code: str
    expires_at: Optional[datetime] = None

    inviter: Optional[User] = None
    channel: Optional[PartialChannel] = None

    def __str__(self) -> str:
        return self.url

    @property
    def url(self) -> str:
        """Formatted invite URL for the invite code."""
        return f'https://discord.gg/{self.code}'

    @property
    def expired(self) -> bool:
        """Whether the invite has expired."""
        if self.expires_at is None:
            return False

        return self.expires_at < datetime.now(timezone.utc)

    @classmethod
    def from_data(cls, data: InviteData) -> Self:
        expires_at = data.get('expires_at')
        if expires_at is not None:
            expires_at = datetime.fromisoformat(expires_at)

        inviter = data.get('inviter')
        if inviter is not None:
            inviter = User.from_data(inviter)

        channel = data.get('channel')
        if channel is not None:
            channel = PartialChannel.from_data(channel)

        return cls(
            code=data['code'],
            expires_at=expires_at,
            inviter=inviter,
            channel=channel
        )
