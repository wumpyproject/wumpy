from typing import Any, Dict

from ..route import Route
from .base import Requester


class GatewayRequester(Requester):
    async def fetch_gateway(self) -> str:
        """Fetch a single valid WSS URL.

        The data this method returns should be cached and will not change.
        """
        d = await self.request(Route('GET', '/gateway'))
        return d['url']

    async def fetch_gateway_bot(self) -> Dict[str, Any]:
        """Fetch a valid WSS URL along with helpful metadata.

        Especially useful when running big bots with shards.
        """
        return await self.request(Route('GET', '/gateway/bot'))
