from ..requester import HTTPXRequester
from .channel import *
from .commands import *
from .gateway import *
from .guild import *
from .guild_template import *
from .interactions import *
from .sticker import *
from .user import *
from .webhook import *


class APIClient(ApplicationCommandRequester, ChannelRequester, GatewayRequester,
                GuildRequester, GuildTemplateRequester, InteractionRequester, StickerRequester,
                UserRequester, WebhookRequester, HTTPXRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
