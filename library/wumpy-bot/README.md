# Wumpy-bot

Easy to use high abstraction over other Wumpy subpackages.

This is the most beginner-friendly way to use Wumpy, and provides all features
of the Discord API. This is the primary package installed from PyPI when you
only specify [`wumpy`](https://pypi.org/project/wumpy/).

## Getting started

All official Wumpy projects prioritise both asyncio and Trio support so you can
run the bot under either:

```python
import anyio
from wumpy.bot import Bot


bot = Bot('ABC123.XYZ789')  # Replace with your token and keep it safe!

# This runs the bot with Trio as the event loop (recommended),
# use backend='asyncio' to run it under asyncio.
anyio.run(bot.run, backend='trio')
```

### Registering listeners

Continuing from the previous code, you can register listeners for Discord
events using Wumpy's rich event listeners:

```python
import anyio
from wumpy.bot import Bot
from wumpy.bot.events import MessageDeleteEvent


bot = Bot('ABC123.XYZ789')


@bot.listener()
async def log_deleted_messages(event: MessageDeleteEvent):
    print(f'Message {event.message_id} in {event.channel_id} was deleted')


anyio.run(bot.run, backend='trio')
```

The listener is registered with the `@bot.listener()` decorator, which tells
Wumpy to read the annotation of the first parameter (name does not matter, but
here it is called `event`) and register that function for the type of event
that it is typehinted as.
