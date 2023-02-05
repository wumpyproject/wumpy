from typing import Optional

import attrs
from typing_extensions import Self

from .._raw import RawBotUser, RawUser
from .._utils import MISSING, get_api
from . import _channels  # Potential circular imports

__all__ = (
    'User',
    'BotUser',
)


@attrs.define(eq=False, frozen=True)
class User(RawUser):
    ...

    async def create_dm(self) -> '_channels.DMChannel':
        """Create a DM with the user to be able to send messages.

        This method (endpoint) is idempotent and will return the same channel
        on subsequent calls.

        Returns:
            The created or reused DM channel.
        """
        data = await get_api().create_dm(self.id)
        return _channels.DMChannel.from_data(data)


@attrs.define(eq=False, frozen=True)
class BotUser(RawBotUser):
    ...

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[str] = MISSING,
    ) -> Self:
        """Edit the current bot user.

        Parameters:
            username: New username to set.
            avatar: New base64-encoded image data for the avatar.

        Returns:
            New instance of the bot user with updated values.
        """
        data = await get_api().edit_my_user(username=username, avatar=avatar)
        return self.__class__.from_data(data)
