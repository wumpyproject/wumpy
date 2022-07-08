from . import endpoints
from ._config import (
    RatelimiterContext,
    abort_if_ratelimited,
)
from ._errors import (
    HTTPException,
    RateLimited,
    Forbidden,
    NotFound,
    ServerException,
)
from ._ratelimiter import (
    Ratelimiter,
    DictRatelimiter,
)
from ._requester import (
    Requester,
    HTTPXRequester,
)
from ._route import (
    Route,
)
from ._utils import (
    MISSING,
)

__all__ = (
    'RatelimiterContext',
    'abort_if_ratelimited',
    'HTTPException',
    'RateLimited',
    'Forbidden',
    'NotFound',
    'ServerException',
    'Ratelimiter',
    'DictRatelimiter',
    'Requester',
    'HTTPXRequester',
    'Route',
    'MISSING',
    'APIClient',
)


class APIClient(endpoints.ApplicationCommandEndpoints, endpoints.ChannelEndpoints,
                endpoints.GatewayEndpoints, endpoints.GuildEndpoints,
                endpoints.GuildTemplateEndpoints, endpoints.InteractionEndpoints,
                endpoints.StickerEndpoints, endpoints.UserEndpoints,
                endpoints.WebhookEndpoints, HTTPXRequester):
    """Requester class with all endpoints inherited."""

    __slots__ = ()
