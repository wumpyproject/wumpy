import anyio

from ..models import Intents

from ..utils import EventDispatcher
from .rest import RESTClient
from .ws import DiscordGateway


class GatewayClient(EventDispatcher):
    ws: DiscordGateway
    api: RESTClient

    def __init__(self, token: str, *, intents: Intents) -> None:
        super().__init__()

        self.token = token
        self.intents = intents

    async def start(self, gateway=DiscordGateway) -> int:
        async with anyio.create_task_group() as tg:
            async with RESTClient(None, token=self.token) as self.api:
                uri = await self.api.fetch_gateway()
                async with gateway.connect(uri, self.token, int(self.intents)) as self.ws:
                    async for data in self.ws:
                        self.dispatch(data['t'], data, tg=tg)

        # True will become 1 (exit code meaning an error occured)
        # False will become 0 (which means the program exited with no error)
        return int(tg.cancel_scope.cancel_called)
