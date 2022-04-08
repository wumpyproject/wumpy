from typing import Any, Optional, SupportsInt

from discord_typings import UserData
from wumpy.models import (
    Category, Emoji, Guild, Invite, Member, Message, Role, Sticker, Thread,
    User
)

from ..protocol import Cache, Channel

__all__ = ('BaseMemoryCache',)


class BaseMemoryCache(Cache):
    """The base for all in-memory caches.

    The point of this is to house the base implementation of the required
    `update()` method, which propogates to the matching processor, allowing for
    one O(1) dictionary lookup on the attributes.
    """

    __slots__ = ()

    async def update(self, payload: dict) -> Any:
        """Propogate the `update()` to a processor.

        Processors needs to follow: `_process_discord_event` naming; starting
        with `_process_` and then the event from Discord but lowercased.

        This method will simply lookup the naming above in the attributes and
        call it.

        Parameters:
            payload: The payload to propogate.

        Returns:
            Whatever the processor returned; if no processor is found, None.
        """
        if 't' not in payload:
            # If the type key is missing, that means that this is not a
            # dispatch event, so there is nothing for us to handle.
            return None

        try:
            processor = getattr(self, f'_process_{payload["t"].lower()}')
        except AttributeError:
            return None

        return await processor(payload)

    async def get_guild(self, guild: SupportsInt) -> Optional[Guild]:
        ...

    async def get_role(self, role: SupportsInt) -> Optional[Role]:
        ...

    async def get_channel(self, channel: SupportsInt) -> Optional[Channel]:
        ...

    async def get_thread(self, thread: SupportsInt) -> Optional[Thread]:
        ...

    async def get_category(self, category: SupportsInt) -> Optional[Category]:
        ...

    async def get_message(
        self,
        channel: Optional[SupportsInt],
        message: SupportsInt
    ) -> Optional[Message]:
        ...

    async def get_emoji(self, emoji: SupportsInt) -> Optional[Emoji]:
        ...

    async def get_sticker(self, sticker: SupportsInt) -> Optional[Sticker]:
        ...

    async def get_invite(self, invite: SupportsInt) -> Optional[Invite]:
        ...

    async def get_member(self, guild: SupportsInt, user: SupportsInt) -> Optional[Member]:
        ...

    async def get_user(self, user: SupportsInt) -> Optional[User]:
        ...

    # Certain caches depend on others to store things for them, we need to
    # define these fallbacks so that they can be safely called without worrying
    # about AttributeErrors trying to access the method.

    def _store_user(self, data: UserData) -> User:
        # This method is overriden by UserMemoryCache and adds the user to the
        # cache - still, in the fallback we can create a user without actually
        # storing it for later.
        return User.from_data(data)
