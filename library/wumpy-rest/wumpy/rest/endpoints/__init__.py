from .base import *
from .channel import *
from .commands import *
from .gateway import *
from .guild_template import *
from .sticker import *
from .user import *
from .webhook import *


class APIClient(ApplicationCommandRequester, ChannelRequester, GatewayRequester,
                GuildTemplateRequester, StickerRequester, UserRequester, WebhookRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
