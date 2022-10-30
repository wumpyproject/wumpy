import attrs

from .._raw import RawInteractionMember, RawMember
from ._user import User


@attrs.define(eq=False)
class Member(RawMember, User):
    ...


@attrs.define(eq=False)
class InteractionMember(RawInteractionMember, Member):
    ...
