from datetime import datetime, timezone
from typing import Optional, Union

import attrs
from discord_typings import InviteCreateData, InviteData
from typing_extensions import Self

from .._raw import PartialChannel, RawInvite
from .._utils import MISSING, get_api
from . import _user

__all__ = (
    'Invite',
)


@attrs.define()
class Invite(RawInvite):
    """Representation of a Discord invite."""

    inviter: Optional[_user.User]  # Override typehint

    @classmethod
    def from_data(cls, data: Union[InviteData, InviteCreateData]) -> Self:
        expires_at = data.get('expires_at')
        if expires_at is not None:
            expires_at = datetime.fromisoformat(expires_at)

        inviter = data.get('inviter')
        if inviter is not None:
            inviter = _user.User.from_data(inviter)

        channel = data.get('channel')
        if channel is not None:
            channel = PartialChannel.from_data(channel)

        return cls(
            code=data['code'],
            expires_at=expires_at,
            inviter=inviter,
            channel=channel
        )
