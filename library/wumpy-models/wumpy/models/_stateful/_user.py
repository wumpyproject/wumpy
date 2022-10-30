from typing import Optional

import attrs
from typing_extensions import Self

from .._raw import RawBotUser, RawUser
from .._utils import MISSING, get_api
from . import _channels  # Potential circular imports

__all__ = (
    'User',
    'RawBotUser',
)


@attrs.define(eq=False)
class User(RawUser):
    ...


@attrs.define(eq=False)
class BotUser(RawBotUser):
    ...
