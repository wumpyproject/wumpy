import attrs

from .._raw import RawRole
from .._utils import MISSING, get_api

__all__ = (
    'Role',
)


@attrs.define(eq=False)
class Role(RawRole):
    ...
