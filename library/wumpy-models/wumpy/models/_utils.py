from datetime import datetime, timezone
from typing import (
    TYPE_CHECKING, Any, Mapping, NoReturn, Optional, SupportsInt, Union
)

import attrs
from typing_extensions import Self

__all__ = (
    'DISCORD_EPOCH',
    'Model',
    'Snowflake',
)


DISCORD_EPOCH = 1420070400000


@attrs.define(frozen=True)
class Model:
    """The root for all Wumpy objects, a Discord object with an ID.

    A Model is a simple wrapper over an integer - the Discord snowflake which
    is guaranteed by Discord to be unique. It tries to support as many
    operations as possible. This class is later used for all models in
    `wumpy-models` that are exposed.

    Attributes:
        id: The underlying integer value representing the Discord snowflake.
    """

    id: int

    def __repr__(self) -> str:
        return f'wumpy.models.Model(id={self.id})'

    def __hash__(self) -> int:
        return self.id >> 22

    def __int__(self) -> int:
        return self.id

    def __float__(self) -> float:
        return float(self.id)

    def __complex__(self) -> complex:
        return complex(self.id)

    def __index__(self) -> int:
        return self.id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return NotImplemented

        return self.id == value

    def __ne__(self, other: object) -> bool:
        # There's a performance hit to not defining __ne__, even though
        # Python will automatically call __eq__ and invert it

        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return NotImplemented

        return self.id != value

    @property
    def created_at(self) -> datetime:
        timestamp = (self.id >> 22) + DISCORD_EPOCH
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


@attrs.define(eq=False, frozen=True)
class Snowflake(Model):
    """Standalone Discord snowflake.

    This is seperate from Model as not all methods on this class should be
    inherited to subclasses, such as the `from_datetime()` classmethod. Any
    standalone ID field will be an instance of this class.

    Attributes:
        id: The underlying integer value representing the Discord snowflake.
    """

    def __init__(self, id: Union[SupportsInt, str]) -> None:
        super().__init__(int(id))

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
    def from_datetime(cls, dt: datetime) -> Self:
        """Craft a snowflake created at the specified time.

        This enables a neat trick for pagination through the Discord API as
        Discord only look at the timestamp it represents.

        Parameters:
            dt: The datetime of when the snowflake should be created.

        Returns:
            The snowflake created at the specified time.
        """
        return cls(int(dt.timestamp() * 1000 - DISCORD_EPOCH) << 22)


def _get_as_snowflake(data: Optional[Mapping[str, Any]], key: str) -> Optional[Snowflake]:
    """Get a key as a snowflake.

    Returns None if `data` is None or does not have the key.

    Parameters:
        data: The optional mapping to get the key from.
        key: The key to attempt to look up.

    Returns:
        The value of the key wrapped in a Snowflake, if there was a mapping
        passed and the key could be found.
    """
    if data is None:
        return None

    value: Union[str, int, None] = data.get(key)
    return Snowflake(int(value)) if value is not None else None

try:
    from wumpy.rest import MISSING, get_api
except ImportError:
    if not TYPE_CHECKING:
        def get_api(subclass: Optional[type] = None, *, verify: bool = False) -> NoReturn:
            raise RuntimeError('There is no currently active API')

        MISSING = object()
