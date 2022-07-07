from . import endpoints
from .config import *
from .errors import *
from .ratelimiter import *
from .requester import *
from .route import *


class APIClient(endpoints.ApplicationCommandEndpoints, endpoints.ChannelEndpoints,
                endpoints.GatewayEndpoints, endpoints.GuildEndpoints,
                endpoints.GuildTemplateEndpoints, endpoints.InteractionEndpoints,
                endpoints.StickerEndpoints, endpoints.UserEndpoints,
                endpoints.WebhookEndpoints, HTTPXRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
