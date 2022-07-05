import dataclasses
from typing import Callable, Optional, Type, Union, overload

from typing_extensions import Self

from .utils import backport_slots

__all__ = (
    'ApplicationFlags', 'Intents', 'MessageFlags', 'UserFlags'
)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class DiscordFlags:
    """The base for all bitfield wrappers.

    This class supports all common bitwise operations which will propagate to
    the underlying integer value. Used for Discord flags and intents.

    Attributes:
        value: The underlying integer value of the flag.
    """

    value: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.value == value

    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.value != value

    def __int__(self) -> int:
        return self.value

    def __float__(self) -> float:
        return float(self.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __and__(self, other: object) -> Self:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value & value)

    def __xor__(self, other: object) -> Self:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value ^ value)

    def __or__(self, other: object) -> Self:
        if isinstance(other, self.__class__):
            value = other.value
        elif isinstance(other, int):
            value = other
        else:
            return NotImplemented

        return self.__class__(self.value | value)

    @classmethod
    def none(cls) -> Self:
        """Construct a flag instance with no set values.

        Returns:
            An instance of this flag with no set values.
        """
        return cls(0)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class BitMask:
    """Representing one bit of a bitfield, using discriptors.

    The memory usage of this class is O(1), n being the amount of instances
    of the BitField class this is attached to.

    Attributes:
        mask: The integer mask of this bit.
    """

    mask: int

    @overload
    def __get__(self, instance: None, cls: Type[DiscordFlags]) -> int:
        ...

    @overload
    def __get__(self, instance: DiscordFlags, cls: Type[DiscordFlags]) -> bool:
        ...

    def __get__(
        self,
        instance: Optional[DiscordFlags],
        cls: Optional[type] = None
    ) -> Union[bool, int]:
        if instance is None:
            return self.mask

        return (instance.value & self.mask) == self.mask


def flag(func: Callable[[], int]) -> BitMask:
    """Flag decorator, converting a method into a BitMask descriptor instance.

    This decorator can only be used on DiscordFlags instances that have a
    `value` attribute, if used on another instance it will fail when trying to
    check a flag.

    The benefit of this decorator over directly instantiating a BitMask is how
    it allows for a docstring to be set for documentation purposes.

    Parameters:
        func: The function containing the bit mask to use.

    Returns:
        A descriptor that will see if the bitfield contains the bit mask.
    """
    return BitMask(func())


@backport_slots()
@dataclasses.dataclass(frozen=True)
class ApplicationFlags(DiscordFlags):
    """Bitfield flags for a Discord application."""

    @flag
    def gateway_presence() -> int:
        """Whether the application is verified and is allowed to receive
        presence information over the gateway.
        """
        return 1 << 12

    @flag
    def gateway_presence_limited() -> int:
        """Whether the application is allowed to receive limited presence
        information over the gateway.
        """
        return 1 << 13

    @flag
    def gateway_guild_members() -> int:
        """Whether the application is verified and is allowed to receive
        member information over the gateway.
        """
        return 1 << 14

    @flag
    def gateway_guild_members_limited() -> int:
        """Whether the application is allowed to receive limited member
        information over the gateway.
        """
        return 1 << 15

    @flag
    def verification_pending_guild_limit() -> int:
        """Whether the application has hit the guild limit, and its
        verification is currently pending.
        """
        return 1 << 16

    @flag
    def embedded() -> int:
        """Whether the application is embedded within the Discord client."""
        return 1 << 17


@backport_slots()
@dataclasses.dataclass(frozen=True)
class Intents(DiscordFlags):
    """Bitfield for Discord gateway intents.

    At scale, the amount of data you're expected to be process can make it very
    hard to maintain a stateful application. Gatway intents allow you to filter
    out groups of specific events from being sent over the gateway - lowering
    your computational burden.

    This intents class is immutable (dataclass frozen) which means that you
    cannot construct intents the same way done in discord.py.

    Usage:

        ```python
        from wumpy.models import Intents

        intents = Intents(
            Intents.guilds | Intents.guild_messages | Intents.guild_bans
        )
        ```

        ```python
        from wumpy.models import Intents

        # All intents except for direct messages
        intents = Intents.all() ^ Intents.direct_messages
        ```
    """

    @overload
    def replace(  # type: ignore  # @overload doesn't have multiple signatures
        self,
        *,
        guilds: bool = ...,
        guild_members: bool = ...,
        guild_bans: bool = ...,
        guild_emojis_and_stickers: bool = ...,
        guild_integrations: bool = ...,
        guild_webhooks: bool = ...,
        guild_invites: bool = ...,
        guild_voice_states: bool = ...,
        guild_presences: bool = ...,
        guild_messages: bool = ...,
        guild_message_reactions: bool = ...,
        guild_message_typing: bool = ...,
        direct_messages: bool = ...,
        direct_message_reactions: bool = ...,
        direct_message_typing: bool = ...,
        messages: bool = ...,
        guild_scheduled_events: bool = ...,
        automod_configuration: bool = ...,
        automod_execution: bool = ...,
    ) -> Self:
        ...

    def replace(self, **kwargs: bool) -> Self:
        cls, value = self.__class__, self.value

        for intent, new in kwargs.items():
            flag = getattr(cls, intent)
            if new:
                value |= flag
            else:
                value &= ~flag

        return cls(value)

    @flag
    def guilds() -> int:
        return 1 << 0

    @flag
    def guild_members() -> int:
        return 1 << 1

    @flag
    def guild_bans() -> int:
        return 1 << 2

    @flag
    def guild_emojis_and_stickers() -> int:
        return 1 << 3

    @flag
    def guild_integrations() -> int:
        return 1 << 4

    @flag
    def guild_webhooks() -> int:
        return 1 << 5

    @flag
    def guild_invites() -> int:
        return 1 << 6

    @flag
    def guild_voice_states() -> int:
        return 1 << 7

    @flag
    def guild_presences() -> int:
        return 1 << 8

    @flag
    def guild_messages() -> int:
        return 1 << 9

    @flag
    def guild_message_reactions() -> int:
        return 1 << 10

    @flag
    def guild_message_typing() -> int:
        return 1 << 11

    @flag
    def direct_messages() -> int:
        return 1 << 12

    @flag
    def direct_message_reactions() -> int:
        return 1 << 13

    @flag
    def direct_message_typing() -> int:
        return 1 << 14

    @flag
    def messages() -> int:
        return 1 << 15

    @flag
    def guild_scheduled_events() -> int:
        return 1 << 16

    @flag
    def automod_configuration() -> int:
        return 1 << 20

    @flag
    def automod_execution() -> int:
        return 1 << 21

    @classmethod
    def all(cls) -> Self:
        return cls(0b111111111111111100011)

    @classmethod
    def default(cls) -> Self:
        return cls.all() ^ cls.guild_presences ^ cls.guild_members ^ cls.messages

    @overload
    @classmethod
    def build(  # type: ignore  # @overload doesn't have multiple signatures
        cls,
        *,
        guilds: bool = False,
        guild_members: bool = False,
        guild_bans: bool = False,
        guild_emojis_and_stickers: bool = False,
        guild_integrations: bool = False,
        guild_webhooks: bool = False,
        guild_invites: bool = False,
        guild_voice_states: bool = False,
        guild_presences: bool = False,
        guild_messages: bool = False,
        guild_message_reactions: bool = False,
        guild_message_typing: bool = False,
        direct_messages: bool = False,
        direct_message_reactions: bool = False,
        direct_message_typing: bool = False,
        messages: bool = False,
        guild_scheduled_events: bool = False,
        automod_configuration: bool = False,
        automod_execution: bool = False,
    ) -> Self:
        ...

    @classmethod
    def build(cls, **kwargs: bool) -> Self:
        value = 0

        for intent in [k for (k, v) in kwargs.items() if v is True]:
            value |= getattr(cls, intent)

        return cls(value)


@backport_slots()
@dataclasses.dataclass(frozen=True)
class MessageFlags(DiscordFlags):
    """Flags for a message object sent by Discord."""

    @flag
    def crossposted() -> int:
        """Whether this message has been published to subscribed channels."""
        return 1 << 0

    @flag
    def is_crosspost() -> int:
        """Whether this message is a crosspost from a message in another channel."""
        return 1 << 1

    @flag
    def supress_embeds() -> int:
        """Whether this message does not include embeds when serializing."""
        return 1 << 2

    @flag
    def source_message_deleted() -> int:
        """Whether the source message for this crosspost has been deleted."""
        return 1 << 3

    @flag
    def urgent() -> int:
        """Whether this message came from the urgent message system."""
        return 1 << 4

    @flag
    def has_thread() -> int:
        """Whether this message is associated with a thread."""
        return 1 << 5

    @flag
    def ephemeral() -> int:
        """Whether this message is only visible to the user who invoked the interaction."""
        return 1 << 6

    @flag
    def loading() -> int:
        """Whether this message is an interaction response with the bot "thinking"."""
        return 1 << 7

    @flag
    def failed_role_mention_in_thread() -> int:
        """Whether this message failed to mention some roles and add their members to a thead."""
        return 1 << 8


@backport_slots()
@dataclasses.dataclass(frozen=True)
class UserFlags(DiscordFlags):
    """Bitfield flags for a Discord user object."""

    @flag
    def employee() -> int:
        """Whether the user is a Discord employee."""
        return 1 << 0

    @flag
    def partner() -> int:
        """Whether the user is a partnered Server owner."""
        return 1 << 1

    @flag
    def hypesquad_events() -> int:
        """Whether the user is a member of the HypeSquad Events team."""
        return 1 << 2

    @flag
    def bug_hunter_level_1() -> int:
        """Whether the user is a level 1 Discord bug hunter."""
        return 1 << 3

    @flag
    def bravery() -> int:
        """Whether the user is part of the HypeSquad Bravery house."""
        return 1 << 6

    @flag
    def brilliance() -> int:
        """Whether the user is part of the HypeSquad Brilliance house."""
        return 1 << 7

    @flag
    def balance() -> int:
        """Whether the user is part of the HypeSquad Balance house."""
        return 1 << 8

    @flag
    def early_supporter() -> int:
        """Whether the user is an early support of Discord."""
        return 1 << 9

    @flag
    def team_user() -> int:
        """Whether the user is a special Discord application team user."""
        return 1 << 10

    @flag
    def bug_hunter_level_2() -> int:
        """Whether the user is a level 2 Discord bug hunter."""
        return 1 << 14

    @flag
    def verified_bot() -> int:
        """Whether the user is a verified Discord bot."""
        return 1 << 16

    @flag
    def verified_bot_developer() -> int:
        """Whether the user is the owner of a Discord bot that was verified early on."""
        return 1 << 17

    @flag
    def certified_moderator() -> int:
        """Whether the user is a Discord certified moderator."""
        return 1 << 18

    @flag
    def http_interactions_bot() -> int:
        """Whether the user is an HTTP-only interactions bot."""
        return 1 << 19
