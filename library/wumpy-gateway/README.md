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
the heartbeating. If you wish to handle this yourself use `create_connection()`
and create an instance from the return value.
