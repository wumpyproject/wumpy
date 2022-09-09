from typing import Any, Callable, TypeVar, overload, Type, cast

from typing_extensions import Final, final

from . import endpoints
from ._requester import HTTPXRequester, _current_api

__all__ = (
    'MISSING',
    'APIClient',
    'get_api',
)


T = TypeVar('T')

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


MISSING: Final[Any] = MissingType()


class APIClient(endpoints.ApplicationCommandEndpoints, endpoints.ChannelEndpoints,
                endpoints.GatewayEndpoints, endpoints.GuildEndpoints,
                endpoints.GuildTemplateEndpoints, endpoints.InteractionEndpoints,
                endpoints.StickerEndpoints, endpoints.UserEndpoints,
                endpoints.WebhookEndpoints, HTTPXRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()


@overload
def get_api(*, verify: bool = False) -> APIClient:
    ...


@overload
def get_api(subclass: Type[T], *, verify: bool = False) -> T:
    ...


def get_api(subclass: Type[T] = APIClient, *, verify: bool = False) -> T:
    """Get the currently active API.

    This function is what powers `wumpy-models`'s ability to make API requests
    without passing an explicit API around.

    Parameters:
        subclass: The type of the return type for the type checker.
        verify: Whether to do an `isinstance()` check on the gotten instance.

    Raises:
        RuntimeError: There is no currently active API.
        RuntimeError: If `verify` is True, the `isinstance()` check failed

    Returns:
        The currently active API.
    """
    try:
        instance = _current_api.get()
    except LookupError:
        raise RuntimeError('There is no currently active API') from None

    if verify and not isinstance(instance, subclass):
        raise RuntimeError(f'Currently active API is not a subclass of {subclass.__name__!r}')

    return cast(T, instance)
