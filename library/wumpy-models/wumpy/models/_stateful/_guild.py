import attrs

from .._raw import RawGuild


@attrs.define(eq=False)
class Guild(RawGuild):
    ...
