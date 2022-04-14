import functools
from typing import (
    Any, Callable, Dict, Generic, Mapping, Optional, Type, TypeVar, Union
)

from wumpy.models import Snowflake

__all__ = ('RuntimeVar',)


T = TypeVar('T')


def _eval_annotations(obj: Callable['...', object]) -> Dict[str, Any]:
    """Eval a callable's annotations.

    This is primarily a backport of Python 3.10's `get_annotations()`
    method implemented by Larry Hastings:
    https://github.com/python/cpython/commit/74613a46fc79cacc88d3eae4105b12691cd4ba20

    Parameters:
        obj: The received callable to evaluate

    Returns:
        A dictionary of parameter name to its annotation.
    """
    unwrapped = obj
    while True:
        if hasattr(unwrapped, '__wrapped__'):
            unwrapped = unwrapped.__wrapped__
            continue
        if isinstance(unwrapped, functools.partial):
            unwrapped = unwrapped.func
            continue
        break

    annotations = getattr(unwrapped, '__annotations__', None)
    eval_globals = getattr(unwrapped, '__globals__', None)

    if annotations is None or not annotations:
        return {}

    if not isinstance(annotations, dict):
        raise ValueError(f'{unwrapped!r}.__annotations__ is neither a dict nor None')

    try:
        return {
            key: value if not isinstance(value, str) else eval(value, eval_globals)
            for key, value in annotations.items()
        }
    except (NameError, SyntaxError) as e:
        raise ValueError(f'Could not evaluate the annotations of {unwrapped!r}') from e


def _get_as_snowflake(data: Optional[Mapping[str, Any]], key: str) -> Optional[Snowflake]:
    """Get a key as a snowflake.

    Returns None if `data` is None or does not have the key. This was copied
    from `wumpy-models`'s `utils.py` file.

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


class RuntimeVar(Generic[T]):
    """Descriptor for attributes that are set during runtime.

    This descriptor raises a `RuntimeError` if the attribute is accessed before
    it has been set - the benefit of which is that you can have attributes that
    should usualy use `Optional[T]` but without the unnecessary runtime checks
    to pass type hinting.

    This is a generic for the type of the underlying value.
    """

    name: Optional[str]
    value: T

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name

    def __set_name__(self, owner: Type[object], name: str) -> None:
        if self.name is not None:
            self.name = name

    def __get__(self, instance: Optional[object], cls: Type[object]) -> T:
        if instance is None:
            raise AttributeError(f'{cls.__name__!r} object has no attribute {self.name!r}')

        if not hasattr(self, 'value'):
            raise RuntimeError(
                f'Cannot access runtime variable {self.name!r} before bot is running'
            )

        return self.value

    def __set__(self, instance: object, value: T) -> None:
        self.value = value
