from typing import Any, Optional, SupportsInt, Tuple, Callable, Dict

import anyio.lowlevel
from discord_typings import UserData
from wumpy.models import (
    Category, Emoji, Guild, Invite, Member, Message, Role, Sticker, Thread,
    User
)

from ..protocol import Cache, Channel

__all__ = ('BaseMemoryCache',)


EventProcessor = Callable[[Dict[str, Any]], Tuple[Optional[Any], Any]]


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
            await anyio.lowlevel.checkpoint()
            return None

        # Because this is a coroutine-function we should await somewhere, but
        # it's best to run the in-memory cache stuff as soon as possible
        # (so that other tasks can't modify the cache). This can't happen after
        # we have successfully updated the cache though as we don't want to get
        # cancelled causing us to both succeed and fail at the same time.
        # Therefore the yielding is split into multiple steps.
        await anyio.lowlevel.checkpoint_if_cancelled()

        try:
            processor: EventProcessor = getattr(self, f"_process_{payload['t'].lower()}")
        except AttributeError:
            return None
        else:
            return processor(payload['d'])
        finally:
            await anyio.lowlevel.cancel_shielded_checkpoint()

    # If we don't define these methods the type checker will complain because
    # we don't implement the protocol

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
