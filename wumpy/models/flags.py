from typing import Any, Callable, Optional, Union

import cython

__all__ = ('Intents',)


@cython.cclass
class BaseFlags:
    """The base for all bitfield wrappers.

    Supports bitwise operators which will propogate the operation to
    the underlying 32-bit integer.
    """

    value = cython.declare(cython.int, visibility='readonly')

    # __slots__ = ('value',)

    def __init__(self, value: cython.int) -> None:
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


@cython.cclass
class BitMask:
    """Representing one bit of a bitfield, using discriptors.

    The memory usage of this class is O(1), n being the amount of instances
    of the BitField class this is attached to.
    """

    mask: cython.int

    __slots__ = ('mask',)

    def __init__(self, mask: cython.int) -> None:
        self.mask = mask

    def __get__(self, instance: BaseFlags, _: Optional[type]) -> Union[bool, int]:
        if instance is None:
            return self.mask

        return (instance.value & self.mask) == self.mask

    def __set__(self, instance: BaseFlags, value: cython.bint) -> None:
        if value is True:
            instance.value |= self.mask
        else:
            instance.value &= ~self.mask


def flag(func: Callable[[Any], int]) -> BitMask:
    """Flag decorator, converting a method into a Bit descriptor instance.

    This decorator can only be used on BaseFlags instances that have a `value` attribute.
    """
    return BitMask(func(None))


@cython.cclass
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
