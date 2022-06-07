import contextlib
import dataclasses
import itertools
import warnings
from typing import (
    Any, Callable, Iterable, Iterator, Mapping, Optional, TypeVar, Union,
    overload
)

from wumpy.rest.utils import MISSING as MISSING

from .base import Snowflake

# Reintroduce MISSING here so that it can be imported easier by models
__all__ = ('MISSING', '_get_as_snowflake')


ClsT = TypeVar('ClsT', bound=type)


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
