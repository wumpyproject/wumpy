from typing import Any, Final, final

__all__ = ('MISSING',)


@final
class MissingType(object):
    """Representing an optional default when no value has been passed.

    This is mainly used as a sentinel value for defaults to work nicely
    with typehints, so that `Optional[X]` doesn't have to be used.
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING: Final[Any] = object()
