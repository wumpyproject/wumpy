from datetime import datetime, timezone
from typing import Any, Type, TypeVar

__all__ = ('Object', 'Snowflake')


DISCORD_EPOCH = 1420070400000


class Object:
    """The root for all Wumpy objects, a Discord object with an ID.

    Stateless by choice so that classes themselves can decide if they want
    to be stateful.
    """

    id: int

    __slots__ = ('id',)

    def __init__(self, id: int) -> None:
        # If we'd include state as optionally None, that would make it
        # annoying to deal with in subclasses when we know state is there
        self.id = id

    def __repr__(self) -> str:
        # To be clear that it isn't a normal object
        return f'<wumpy.Object id={self.id}>'

    def __hash__(self) -> int:
        return self.id >> 22

    def __int__(self) -> int:
        return self.id

    def __float__(self) -> float:
        return float(self.id)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return False

        return self.id == value

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return True

        return self.id != value

    @property
    def created_at(self) -> datetime:
        timestamp = (self.id >> 22) + DISCORD_EPOCH
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


# We need to type the return type of the from_datetime() classmethod
SELF = TypeVar('SELF', bound='Snowflake')


class Snowflake(Object):
    """Standalone Discord snowflake.

    This is seperate from Object as not all methods on this class should be
    inherited to subclasses, such as the `from_datetime()` classmethod. Any
    standalone ID field will be an instance of this class.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f'<Snowflake id={self.id}>'

    @property
    def worker_id(self) -> int:
        """Return the ID of the worker that created the snowflake."""
        return (self.id & 0x3E0000) >> 17

    @property
    def process_id(self) -> int:
        """Return the ID of the process that created the snowflake."""
        return (self.id & 0x1F000) >> 12

    @property
    def process_increment(self) -> int:
        """Return the increment of the process that created the snowflake."""
        return self.id & 0xFFF

    @classmethod
    def from_datetime(cls: Type[SELF], dt: datetime) -> SELF:
        """Craft a snowflake created at the specified time."""
        return cls(int(dt.timestamp() * 1000 - DISCORD_EPOCH) << 22)
