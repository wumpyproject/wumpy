from datetime import datetime, timezone
from typing import Optional, Union

import attrs
from discord_typings import InviteCreateData, InviteData
from typing_extensions import Self

from ._channels import PartialChannel
from ._user import RawUser

__all__ = (
    'RawInvite',
)


@attrs.define(frozen=True)
class RawInvite:
    """Representation of a Discord invite."""

    code: str
    expires_at: Optional[datetime] = attrs.field(default=None, kw_only=True)

    inviter: Optional[RawUser] = attrs.field(default=None, kw_only=True)
    channel: Optional[PartialChannel] = attrs.field(default=None, kw_only=True)

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
    def from_data(cls, data: Union[InviteData, InviteCreateData]) -> Self:
        expires_at = data.get('expires_at')
        if expires_at is not None:
            expires_at = datetime.fromisoformat(expires_at)

        inviter = data.get('inviter')
        if inviter is not None:
            inviter = RawUser.from_data(inviter)

        channel = data.get('channel')
        if channel is not None:
            channel = PartialChannel.from_data(channel)

        return cls(
            code=data['code'],
            expires_at=expires_at,
            inviter=inviter,
            channel=channel
        )
