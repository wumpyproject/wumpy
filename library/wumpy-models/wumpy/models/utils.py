from typing import Any, Mapping, Optional, Union

from wumpy.rest.utils import MISSING as MISSING

from .base import Snowflake

# Reintroduce MISSING here so that it can be imported easier by models
__all__ = ('MISSING', '_get_as_snowflake')


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
