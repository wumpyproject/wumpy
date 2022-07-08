from discord_typings import GetGatewayBotData

from .._requester import Requester
from .._route import Route

__all__ = (
    'GatewayEndpoints',
)


class GatewayEndpoints(Requester):
    """Endpoints for getting Discord gateway information."""

    __slots__ = ()

    async def fetch_gateway(self) -> str:
        """Fetch a single valid WSS URL.

        The data this method returns should be cached and will not change.

        Returns:
            The URL to connect with a WebSocket to.
        """
        d = await self.request(Route('GET', '/gateway'))
        return d['url']

    async def fetch_gateway_bot(self) -> GetGatewayBotData:
        """Fetch a valid WSS URL along with helpful metadata.

        Especially useful when running big bots with shards, the data returned
        by this call can change per-call as the bot joins/leaves guilds.

        Returns:
            Useful metadata about the gateway when connecting.
        """
        return await self.request(Route('GET', '/gateway/bot'))
