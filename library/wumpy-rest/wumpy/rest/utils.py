from typing import Any, BinaryIO

from typing_extensions import Final, final

__all__ = ('MISSING', 'dump_json', 'load_json')

try:
    import orjson

    dump_json = orjson.dumps
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


MISSING: Final[Any] = MissingType()


class File:
    """Representing a file to be uploaded to Discord."""

    source: BinaryIO
    filename: str

    __slots__ = ('source', 'filename')

    def __init__(self, source: BinaryIO, filename: str, *, spoiler: bool = False) -> None:
        self.source = source

        # We use the removeprefix methods as they do nothing if the string does not
        # start with the string passed.
        if not spoiler:
            self.filename = filename.removeprefix('SPOILER_')
        else:
            # The user may have already added a SPOILER_ prefix
            self.filename = 'SPOILER_' + filename.removeprefix('SPOILER_')

    def read(self, n: int) -> bytes:
        return self.source.read(n)

    def close(self) -> None:
        return self.source.close()
