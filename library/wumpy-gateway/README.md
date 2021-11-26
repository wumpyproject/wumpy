# Wumpy-gateway

Gateway implementation for the Wumpy project.

## Installation

Wumpy-gateway is available as a package on PyPI. Just use your favourite
package manager such as pip or Poetry:

```bash
# Installing from PyPI using pip:
pip install wumpy-gateway
```

```bash
# Alternatively, using Poetry:
poetry add wumpy-gateway
```

## Quickstart

The easiest - and recommended - way to get started is using `Shard.connect()`:

```python
from wumpy.gateway import Shard


INTENTS = 65535
TOKEN = 'ABC123.XYZ789'


async def main():
    # Connect to the URI wss://gateway.discord.gg/ with the token
    # ABC123.XYZ8789 and all intents.
    async with Shard.connect('wss://gateway.discord.gg/', TOKEN, INTENTS) as ws:
        async for event in ws:
            print(event)  # The deserialized JSON event payload
```

The `connect()` classmethod is an abstraction that also spawns a task to handle
the heartbeating. It is not recommended but can re-implemented like this:

```python
import anyio
from wumpy.gateway import Shard


TOKEN = 'ABC123.XYZ789'


async def handle_event(event):
    print(event)


async def main():
    conn, sock = await Shard.create_connection(
        'wss://gateway.discord.gg/', TOKEN, INTENTS
    )
    ws = Shard(conn, sock, TOKEN, INTENTS)
    async with anyio.create_task_group() as tg:
        tg.start_soon(ws.run_heartbeater)

        try:
            async for event in ws:
                await handle_event(event)
        finally:
            # Cancel the heartbeater task - otherwise this will loop forever
            tg.cancel_scope.cancel()

            # Cleanup the gateway connection (handles closing the socket)
            await ws.aclose()
```
