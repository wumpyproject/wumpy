import contextlib
import dataclasses
import itertools
import warnings
from datetime import datetime, timezone
from typing import (
    Any, Callable, Iterable, Iterator, Mapping, Optional, SupportsInt, TypeVar,
    Union, overload
)

from typing_extensions import Self

__all__ = (
    'DISCORD_EPOCH',
    'Model',
    'Snowflake',
)


DISCORD_EPOCH = 1420070400000

ClsT = TypeVar('ClsT', bound=type)


@dataclasses.dataclass(frozen=True)
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

    __slots__ = ('id', '__weakref__')
    __match_args__ = ('id',)

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


@dataclasses.dataclass(frozen=True)
class Snowflake(Model):
    """Standalone Discord snowflake.

    This is seperate from Model as not all methods on this class should be
    inherited to subclasses, such as the `from_datetime()` classmethod. Any
    standalone ID field will be an instance of this class.

    Attributes:
        id: The underlying integer value representing the Discord snowflake.
    """

    __slots__ = ()

    def __init__(self, id: Union[SupportsInt, str]) -> None:
        super().__init__(int(id))

    def __repr__(self) -> str:
        return f'wumpy.models.Snowflake(id={self.id})'

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


@overload
def backport_slots(cls: ClsT) -> ClsT:
    ...


@overload
def backport_slots(*, weakref_slot: bool = True) -> Callable[[ClsT], ClsT]:
    ...


def backport_slots(
        cls: ClsT = None,
        *,
        weakref_slot: bool = True
) -> Union[Callable[[ClsT], ClsT], ClsT]:
    """Backport slots to the dataclass.

    This decorator mirros the behaviour of passing `slots=True` to the original
    `@dataclasses.dataclass()` decorator. The downside is that it has to create
    a new class from the old one.

    This decorator can be called both with- and without paranthesis, which
    means that the `cls` parameter is optional depending on how it was called.

    Parameters:
        cls: The class to recreate with slots
        weakref_slot: Whether to include `__weakref__` in the slots.

    Returns:
        A new class with the specified slots.
    """
    def decorator(cls: ClsT) -> ClsT:
        return _add_slots(cls, weakref_slot=weakref_slot)

    if cls is not None:
        return decorator(cls)

    return decorator


def _backported_get_slots(cls: type) -> Iterable[str]:
    _slots: Union[Iterable[str], Iterator[str], None] = cls.__dict__.get('__slots__')
    # if _slots_ is None, it turns into an empty tuple
    cls_slots = (_slots,) if isinstance(_slots, str) else (_slots or ())
    if hasattr(cls_slots, '__next__'):
        # Slots may be an iterable, but we cannot handle an iterator because it
        # will already be (partially) consumed.
        raise TypeError(f'Slots of {cls.__name__!r} cannot be determined')
    return cls_slots


def _backported_slots(cls, *, weakref_slot):
    """Backport of the internal `_add_slots()` function in dataclasses.

    This is a slightly modified version of the function used by dataclasses to
    create slots for dataclasses that pass `slots=True`. The difference is that
    the functionality of `_get_slots()` is brought into the function and it
    doesn't fix pickling of frozen classes (as to backport as small amount of
    code as possible).

    `__slots__` for dataclasses was first introduced by Yurii Karabas (see the
    first link), but this was copied from the most recent version of
    dataclasses at the time (see the second link):
    - https://github.com/python/cpython/commit/c24199184bea0c851c1a7296ae54aaf18ee56752
    - https://github.com/python/cpython/commit/5f9c0f5ddf441dedeb085b0d9f9c9488ca6bd44d
    """
    # Need to create a new class, since we can't set __slots__
    # after a class has been created.

    # Make sure __slots__ isn't already set.
    if '__slots__' in cls.__dict__:
        raise TypeError(f'{cls.__name__} already specifies __slots__')

    # Create a new dict for our new class.
    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name for f in dataclasses.fields(cls))

    # Make sure slots don't overlap with those in base classes.
    inherited_slots = set(
        itertools.chain.from_iterable(map(_backported_get_slots, cls.__mro__[1:-1]))
    )
    # The slots for our class.  Remove slots from our base classes.  Add
    # '__weakref__' if weakref_slot was given.
    cls_dict['__slots__'] = tuple(
        itertools.chain(
            itertools.filterfalse(inherited_slots.__contains__, field_names),
            ('__weakref__',) if weakref_slot and '__weakref__' not in inherited_slots else ())
    )

    for field_name in field_names:
        # Remove our attributes, if present. They'll still be
        #  available in _MARKER.
        cls_dict.pop(field_name, None)

    # Remove __dict__ itself.
    cls_dict.pop('__dict__', None)

    # And finally create the class.
    qualname = getattr(cls, '__qualname__', None)
    cls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
    if qualname is not None:
        cls.__qualname__ = qualname

    return cls


if hasattr(dataclasses, '_add_slots'):
    def _add_slots(cls, *, weakref_slot):
        with contextlib.suppress(TypeError):
            return dataclasses._add_slots(cls, True, weakref_slot)  # type: ignore

        if not weakref_slot:
            with contextlib.suppress(TypeError):
                # What may be the case here is that we're on Python 3.10
                # and don't have the 'weakref_slot' parameter. If it is
                # False anyways we might as well just use the original.
                return dataclasses._add_slots(cls, True)  # type: ignore

        # Presumably something was changed in the internal function's signature
        # so we need to use the backport. If the TypeError originated from
        # an actual error with the parameters our backport will produce the
        # same error so we aren't accidentally masking erros.

        # Sending a warning here so that it isn't forgotten. This will be
        # discovered in tests.
        warnings.warn(
            'Having to use backported function to add slots when real is available',
            RuntimeWarning
        )
        return _backported_slots(cls, weakref_slot=weakref_slot)
else:
    # Pyright complains about the re-definition of _add_slots
    _add_slots = _backported_slots  # type: ignore


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
