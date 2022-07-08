from ._channel import (
    ChannelMemoryCache,
    MessageMemoryCache,
)
from ._guild import (
    EmojiMemoryCache,
    GuildMemoryCache,
    RoleMemoryCache,
)
from ._user import (
    MemberMemoryCache,
    UserMemoryCache,
)


__all__ = (
    'ChannelMemoryCache',
    'MessageMemoryCache',
    'EmojiMemoryCache',
    'GuildMemoryCache',
    'RoleMemoryCache',
    'MemberMemoryCache',
    'UserMemoryCache',
    'InMemoryCache',
)


class InMemoryCache(ChannelMemoryCache, EmojiMemoryCache, GuildMemoryCache, MemberMemoryCache,
                    MessageMemoryCache, RoleMemoryCache, UserMemoryCache):
    """Cache implementation storing data in local memory."""

    __slots__ = ()
