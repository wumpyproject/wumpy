from typing import Any, Callable

from typing_extensions import Final, final

__all__ = ('MISSING',)


dump_json: Callable[[Any], str]
load_json: Callable[[str], Any]

try:
    import orjson

    def orjson_compat(obj: Any) -> str:
        return orjson.dumps(obj).decode('utf-8')
    dump_json = orjson_compat
    load_json = orjson.loads

except ImportError:
    import json

    dump_json = json.dumps
    load_json = json.loads


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


MISSING: Final[object] = MissingType()
