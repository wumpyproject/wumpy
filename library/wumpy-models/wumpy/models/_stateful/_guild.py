import attrs

from .._raw import RawGuild

__all__ = (
    'Guild',
)

@attrs.define(eq=False, frozen=True)
class Guild(RawGuild):
    ...
