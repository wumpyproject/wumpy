"""Gateway implementation for the Wumpy project.

This module contains a main `Shard` class, to get started import it and use the
`connect()` classmethod as an asynchronous context manager:

```python
from wumpy.gateway import Shard


TOKEN = 'ABC123.XYZ789'
INTENTS = 65535


async def main():
    # Connect to the URI wss://gateway.discord.gg/ with the token
    # ABC123.XYZ8789 and all intents.
    async with Shard.connect('wss://gateway.discord.gg/', TOKEN, INTENTS) as ws:
        async for event in ws:
            print(event)  # The deserialized JSON event payload
```
"""

from .errors import *
from .shard import *
from .utils import DefaultGatewayLimiter
