from .base import *
from .channel import *
from .gateway import *
from .sticker import *
from .user import *
from .webhook import *


class APIClient(ChannelRequester, GatewayRequester, StickerRequester, UserRequester,
                WebhookRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
