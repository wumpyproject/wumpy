from types import TracebackType
from typing import Any, Dict, Optional, SupportsInt, Type, Union

from typing_extensions import Protocol, Self
from wumpy.models import (
    Category, Emoji, Guild, Member, Message, Role, Sticker, TextChannel,
    Thread, User, VoiceChannel
)

__all__ = ['Cache']


Channel = Union[VoiceChannel, TextChannel]


class Cache(Protocol):
    """Protocol for a cache implementation for Wumpy.

    This is not the default implementation for the cache, rather it is the
    typehint that should be used for the cache. All methods return None, so
    this can be used if you do not wish to implement a cache.
    """

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        ...

    async def update(
            self,
            payload: Dict[str, Any],
            *,
            return_old: bool = True
    ) -> Optional[Any]:
        """Update the cache with new information from an event.

        This method should return the old value in the cache if `return_old` is
        `True`. If `return_old` is `False`, that means that no event will be
        dispatched with the returnd value so it is unnecessary to construct.

        Parameters:
            payload:
                The dictionary representation of the payload received by
                Discord over the gateway.
            return_old: Whether to return the old value in the cache.

        Returns:
            The old value replaced by the incoming event, or `None`.
        """
        ...

    async def get_guild(self, guild: SupportsInt) -> Optional[Guild]:
        """Get a guild model from cache.

        Parameters:
            guild: The ID of the guild to get data for.

        Returns:
            A guild model representation, if found in the cache.
        """
        ...

    async def get_role(self, role: SupportsInt) -> Optional[Role]:
        """Get a role from the cache.

        Parameters:
            role: The ID of the role to get the data for.

        Returns:
            The Role model representation, if found in the cache.
        """
        ...

    async def get_channel(self, channel: SupportsInt) -> Optional[Channel]:
        """Get a channel from the cache.

        Parameters:
            channel: The ID of the channel.

        Returns:
            The Channel model representation, if found in the cache.
        """
        ...

    async def get_thread(self, thread: SupportsInt) -> Optional[Thread]:
        """Get a thread from the cache.

        Parameters:
            thread: The ID of the thread.

        Returns:
            The Thread model representation, if found in the cache.
        """
        ...

    async def get_category(self, category: SupportsInt) -> Optional[Category]:
        """Get a category from the cache.

        Parameters:
            category: The ID of the category.

        Returns:
            The Category model representation, if found in the cache.
        """
        ...

    async def get_message(
        self,
        channel: Optional[SupportsInt],
        message: SupportsInt
    ) -> Optional[Message]:
        """Get a message from the cache.

        Parameters:
            channel:
                The ID of the channel the message is in, if it is available.
                This can be None for the freedom of the user and since the
                cache may not require it to look up the message.
            message: The ID of the message.

        Returns:
            The Message model representation, if found in the cache.
        """
        ...

    async def get_emoji(self, emoji: SupportsInt) -> Optional[Emoji]:
        """Get an emoji from the cache.

        Parameters:
            emoji: The ID of the emoji.

        Returns:
            The Emoji model representation, if found in the cache.
        """
        ...

    async def get_sticker(self, sticker: SupportsInt) -> Optional[Sticker]:
        """Get a sticker from the cache.

        Parameters:
            sticker: The ID of the sticker.

        Returns:
            The Sticker model representation, if found in the cache.
        """
        ...

    async def get_member(self, guild: SupportsInt, user: SupportsInt) -> Optional[Member]:
        """Get a member from a guild from the cache.

        Parameters:
            guild: The ID of the guild the user is in.
            user: The ID of the user.

        Returns:
            The Member model representation, if found in the cache.
        """
        ...

    async def get_user(self, user: SupportsInt) -> Optional[User]:
        """Get a user from the cache.

        Parameters:
            user: The ID of the user.

        Returns:
            The User model representation, if found in the cache.
        """
        ...
