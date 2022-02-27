from typing import Any, Generator, NoReturn

import anyio
from wumpy.gateway import Shard
from wumpy.rest import APIClient

from .dispatch import EventDispatcher

__all__ = ('Bot',)


class Bot(EventDispatcher):
    """Main representation of a gateway-based Discord bot.

    Examples:

        ```python
        import anyio
        from wumpy.bot import Bot


        bot = Bot('ABC123.XYZ789', intents=65535)


        # Run the bot with no registered events or commands.
        anyio.run(bot)
        ```
    """

    def __init__(self, token: str, *, intents: int) -> None:
        self.token = token
        self.intents = intents

    def __await__(self) -> Generator[Any, None, NoReturn]:
        return self.run().__await__()

    # This can in fact return, if the WebSocket connection closes or similar.
    # Which is why PyRight complains that it can return None, hence the
    # 'type: ignore' comment. That said, this SHOULD never return in a
    # typical use-case, and NoReturn means that IDEs can help the user by
    # making code after it greyed out or marking it as an error.
    async def run(self) -> NoReturn:  # type: ignore
        async with anyio.create_task_group() as self.tasks:
            async with APIClient(headers={'Authorization': f'Bot {self.token}'}) as self.api:
                link = await self.api.fetch_gateway()
                async with Shard(link, self.token, int(self.intents)) as self.ws:
                    async for data in self.ws:
                        self.dispatch(data['t'], data, tg=self.tasks)
