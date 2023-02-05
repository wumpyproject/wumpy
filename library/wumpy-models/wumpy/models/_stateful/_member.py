import attrs

from .._raw import RawInteractionMember, RawMember
from ._user import User

__all__ = (
    'Member',
    'InteractionMember',
)


@attrs.define(eq=False, frozen=True)
class Member(RawMember, User):
    ...


@attrs.define(eq=False, frozen=True)
class InteractionMember(RawInteractionMember, Member):
    ...
