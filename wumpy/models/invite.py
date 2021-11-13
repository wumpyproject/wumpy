from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .channels import PartialChannel

__all__ = ('Invite',)


class Invite:
    """Representation of a Discord invite."""

    code: str

    channel: PartialChannel
    inviter: Optional[Dict[str, Any]]

    expires_at: Optional[datetime]

    __slots__ = ('code', 'channel', 'inviter', 'expires_at')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.code = data['code']

        self.channel = PartialChannel(data['channel'])
        self.inviter = data.get('inviter')

        expires_at = data.get('expires_at')
        if expires_at:
            expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        self.expires_at = expires_at

    def __str__(self) -> str:
        return self.url

    @property
    def url(self) -> str:
        """Formatted invite URL for the invite code."""
        return f'https://discord.gg/{self.code}'

    @property
    def is_expired(self) -> bool:
        """Whether the invite has expired."""
        if self.expires_at is None:
            return False

        return self.expires_at < datetime.now(timezone.utc)
