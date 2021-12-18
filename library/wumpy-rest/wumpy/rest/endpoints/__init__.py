from .base import *
from .sticker import *
from .user import *


class APIClient(StickerRequester, UserRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
