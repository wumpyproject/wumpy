from typing import (
    Any, AsyncContextManager, Dict, Optional, Protocol, SupportsInt, Tuple,
    Union
)

from wumpy.models import (
    Category, DMChannel, Emoji, Guild, Member, Message,
    Role, Sticker, TextChannel, Thread, User, VoiceChannel
)

__all__ = ['Cache', 'CacheProtocol']


Channel = Union[VoiceChannel, TextChannel]


class Cache(Protocol):
    """Protocol for a cache implementation for Wumpy.

    This is not the default implementation for the cache, rather it is the
    typehint that should be used for the cache. All methods return None, so
    this can be used if you do not wish to implement a cache.
    """

    async def update(self, payload: Dict[str, Any]) -> Tuple[Optional[Any], Optional[Any]]:
        """Update the cache with new information from an event.

        This method should return a tuple with two items depicting the old
        model that was stored in the cache and the new model that was created.

        Because of the huge amounts of types of events that Discord sends it is
        not worth it to document the specific return types per event, but here
        are the rules to follow:

        - Events that CREATE new data should return the model that was created.
          Even if the data was not used to create a model, one should be
          returned to then be dispatched to the user. Since there is no
          previous data the first item will always be None.

        - Events that UPDATE existing data should return the older data if
          present in the cache. That way it can be used by the user. Both
          items of the tuple may be used for the old model, and the new one.

        - Events that DELETE objects should return the existing data if it can
          be found in the cache. This should be in the first item because it is
          older data, the second item should be None because there is no new
          model that is created.

        - All other events, such as RESUMED or TYPING_START which does not have
          any data should return None for both items.

        Parameters:
            payload:
                The dictionary representation of the payload received by
                Discord over the gateway.

        Returns:
            A tuple with two items (models) depicting the old model that was
            popped and the new model that was created `(old, new)`.
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


CacheProtocol = AsyncContextManager[Cache]
