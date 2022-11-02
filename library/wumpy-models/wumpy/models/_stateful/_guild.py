import attrs

from .._raw import RawGuild

__all__ = (
    'Guild',
)

@attrs.define(eq=False)
class Guild(RawGuild):
    ...
