from .base import *
from .channel import *
from .guild import *
from .user import *


class InMemoryCache(ChannelMemoryCache, EmojiMemoryCache, GuildMemoryCache, MemberMemoryCache,
                    MessageMemoryCache, RoleMemoryCache, UserMemoryCache):
    """Cache implementation storing data in local memory."""

    __slots__ = ()
