from typing import Any, Callable, List, Optional, Union

__all__ = (
    'AllowedMentions', 'ApplicationFlags', 'Intents',
    'MessageFlags', 'UserFlags'
)


class BaseFlags:
    """The base for all bitfield wrappers.

    Supports bitwise operators which will propogate the operation to
    the underlying 32-bit integer.
    """

    value: int

    __slots__ = ('value',)

    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not isinstance(other, self.__class__) or self.value != other.value

    def __int__(self) -> int:
        return self.value

    def __float__(self) -> float:
        return float(self.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __and__(self, other: Any) -> Any:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value & value)

    def __xor__(self, other: Any) -> Any:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value ^ value)

    def __or__(self, other: Any) -> Any:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value | value)

    def __invert__(self) -> 'BaseFlags':
        return self.__class__(~self.value)


class BitMask:
    """Representing one bit of a bitfield, using discriptors.

    The memory usage of this class is O(1), n being the amount of instances
    of the BitField class this is attached to.
    """

    mask: int

    __slots__ = ('mask',)

    def __init__(self, mask: int) -> None:
        self.mask = mask

    def __get__(self, instance: BaseFlags, _: Optional[type]) -> Union[bool, int]:
        if instance is None:
            return self.mask

        return (instance.value & self.mask) == self.mask

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        if value is True:
            instance.value |= self.mask
        elif value is False:
            instance.value &= ~self.mask
        else:
            raise TypeError(f'Expected type bool but got {type(value)}.')


def flag(func: Callable[[Any], int]) -> BitMask:
    """Flag decorator, converting a method into a Bit descriptor instance.

    This decorator can only be used on BaseFlags instances that have a `value` attribute.
    """
    return BitMask(func(None))


class AllowedMentions:
    """Discord allowed mentions object."""

    roles: Union[bool, List[int], None]
    users: Union[bool, List[int], None]

    everyone: Optional[bool]
    replied_user: Optional[bool]

    __slots__ = ('roles', 'users', 'everyone', 'replied_user')

    def __init__(
        self,
        *,
        roles: Union[bool, List[int], None] = None,
        users: Union[bool, List[int], None] = None,
        everyone: Optional[bool] = None,
        replied_user: Optional[bool] = None
    ) -> None:
        self.roles = roles
        self.users = users
        self.everyone = everyone
        self.replied_user = replied_user

    @staticmethod
    def _merge(one: Optional[Any], other: Optional[Any]) -> Optional[Any]:
        """Helper function when merging to optional values."""
        if one is None or other is None:
            # Find and return the one that isn't None
            return other if one is None else one
        else:
            # If both are set, we prioritize the right-hand
            # because it should be the most recent
            return other

    # It's hard to type the return type of this, because of NotImplemented
    def __or__(self, other: Any) -> Any:
        if not isinstance(other, self.__class__):
            return NotImplemented

        roles = self._merge(self.roles, other.roles)
        users = self._merge(self.users, other.users)

        everyone = self._merge(self.everyone, other.everyone)
        replied_user = self._merge(self.replied_user, other.replied_user)

        return self.__class__(roles=roles, users=users, everyone=everyone, replied_user=replied_user)


class ApplicationFlags(BaseFlags):
    """Flags for a Discord application."""

    __slots__ = ()

    @flag
    def gateway_presence(_) -> int:
        """Whether the application is verified and is allowed to receive
        presence information over the gateway.
        """
        return 1 << 12

    @flag
    def gateway_presence_limited(_) -> int:
        """Whether the application is allowed to receive limited presence
        information over the gateway.
        """
        return 1 << 13

    @flag
    def gateway_guild_members(_) -> int:
        """Whether the application is verified and is allowed to receive
        member information over the gateway.
        """
        return 1 << 14

    @flag
    def gateway_guild_members_limited(_) -> int:
        """Whether the application is allowed to receive limited member
        information over the gateway.
        """
        return 1 << 15

    @flag
    def verification_pending_guild_limit(_) -> int:
        """Whether the application has hit the guild limit, and is
        verification is currently pending.
        """
        return 1 << 16

    @flag
    def embedded(_) -> int:
        """Whether the application is embedded within the Discord client."""
        return 1 << 17


class Intents(BaseFlags):
    """Discord's gateway flags for managing what events will be received."""

    __slots__ = ()

    @flag
    def guilds(_) -> int:
        return 1 << 0

    @flag
    def guild_members(_) -> int:
        return 1 << 1

    @flag
    def guild_bans(_) -> int:
        return 1 << 2

    @flag
    def guild_emojis_and_stickers(_) -> int:
        return 1 << 3

    @flag
    def guild_integrations(_) -> int:
        return 1 << 4

    @flag
    def guild_webhooks(_) -> int:
        return 1 << 5

    @flag
    def guild_invites(_) -> int:
        return 1 << 6

    @flag
    def guild_voice_states(_) -> int:
        return 1 << 7

    @flag
    def guild_presences(_) -> int:
        return 1 << 8

    @flag
    def guild_messages(_) -> int:
        return 1 << 9

    @flag
    def guild_message_reactions(_) -> int:
        return 1 << 10

    @flag
    def guild_message_typing(_) -> int:
        return 1 << 11

    @flag
    def direct_messages(_) -> int:
        return 1 << 12

    @flag
    def direct_message_reactions(_) -> int:
        return 1 << 13

    @flag
    def direct_message_typing(_) -> int:
        return 1 << 14


class MessageFlags(BaseFlags):
    """Flags for a message object."""

    __slots__ = ()

    @flag
    def crossposted(_) -> int:
        """Whether this message has been published to subscribed channels."""
        return 1 << 0

    @flag
    def is_crosspost(_) -> int:
        """Whether this message is a crosspost from a message in another channel."""
        return 1 << 1

    @flag
    def supress_embeds(_) -> int:
        """Whether this message does not include embeds when serializing."""
        return 1 << 2

    @flag
    def source_message_deleted(_) -> int:
        """Whether the source message for this crosspost has been deleted."""
        return 1 << 3

    @flag
    def urgent(_) -> int:
        """Whether this message came from the urgent message system."""
        return 1 << 4

    @flag
    def has_thread(_) -> int:
        """Whether this message is associated with a thread."""
        return 1 << 5

    @flag
    def ephemeral(_) -> int:
        """Whether this message is only visible to the user who invoked the interaction."""
        return 1 << 6

    @flag
    def loading(_) -> int:
        """Whether this message is an interaction response with the bot "thinking"."""
        return 1 << 7


class UserFlags(BaseFlags):
    """Flags for a Discord user object."""

    __slots__ = ()

    @flag
    def employee(_) -> int:
        """Whether the user is a Discord employee."""
        return 1 << 0

    @flag
    def partner(_) -> int:
        """Whether the user is a partnered Server owner."""
        return 1 << 1

    @flag
    def hypesquad_events(_) -> int:
        """Whether the user is a member of the HypeSquad Events team."""
        return 1 << 2

    @flag
    def bug_hunter_level_1(_) -> int:
        """Whether the user is a level 1 Discord bug hunter."""
        return 1 << 3

    @flag
    def bravery(_) -> int:
        """Whether the user is part of the HypeSquad Bravery house."""
        return 1 << 6

    @flag
    def brilliance(_) -> int:
        """Whether the user is part of the HypeSquad Brilliance house."""
        return 1 << 7

    @flag
    def balance(_) -> int:
        """Whether the user is part of the HypeSquad Balance house."""
        return 1 << 8

    @flag
    def early_supporter(_) -> int:
        """Whether the user is an early support of Discord."""
        return 1 << 9

    @flag
    def team_user(_) -> int:
        """Whether the user is a special Discord application team user."""
        return 1 << 10

    @flag
    def bug_hunter_level_2(_) -> int:
        """Whether the user is a level 2 Discord bug hunter."""
        return 1 << 14

    @flag
    def verified_bot(_) -> int:
        """Whether the user is a verified Discord bot."""
        return 1 << 16

    @flag
    def verified_bot_developer(_) -> int:
        """Whether the user is the owner of a Discord bot that was verified early on."""
        return 1 << 17

    @flag
    def certified_moderator(_) -> int:
        """Whether the user is a Discord certified moderator."""
        return 1 << 18
