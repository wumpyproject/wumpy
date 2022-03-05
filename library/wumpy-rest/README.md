# Wumpy-rest

Richly and accurately typed wrapper around the Discord REST API.

## Usage

The best way to use `wumpy-rest` is to import `APIClient`:

```python
import anyio
from wumpy.rest import APIClient


TOKEN = 'ABC123.XYZ789'


async def main():
    async with APIClient(headers={'Authentication': f'Bot {TOKEN}'}) as api:
        print(await api.fetch_my_user())


anyio.run(main)
```

`APIClient` is a class that implements all routes of the Discord API. This is
made up of multiple route classes. You can create your own class with the
routes you use:

```python
from wumpy.rest import ApplicationCommandRequester, InteractionRequester


class MyAPIClient(ApplicationCommandRequester, InteractionRequester):

    __slots__ = ()  # Save some memory for this class
```

### Files

Some endpoints support uploading files, for these a file-like object is
expected that's been opened in binary-mode (for example `'rb'`).

For the message/interaction endpoints, remember to include a matching
`attachment` object with `'id'` set to the index of the file.

## Ratelimiter

You can pass a custom ratelimiter to the requester if you want to customize
that behaviour. For more, [read the documentation](https://wumpy.rtfd.io).
Here's an example of a ratelimiter that does no ratelimiting and does not
handle any kind of `429`-responses.

```python
from contextlib import asynccontextmanager
from typing import (
    Any, AsyncContextManager, AsyncGenerator, Awaitable, Callable, Coroutine,
    Mapping
)

import anyio
from wumpy.rest import APIClient


class NoOpRatelimiter:
    """Ratelimiter implementation that does nothing; a no-op implementation."""

    async def __aenter__(self) -> Callable[
        [Route], AsyncContextManager[
            Callable[[Mapping[str, str]], Awaitable]
        ]
    ]:
        return self.acquire

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> object:
        pass

    async def update(self, headers: Mapping[str, str]) -> object:
        pass

    @asynccontextmanager
    async def acquire(self, route: Route) -> AsyncGenerator[
        Callable[[Mapping[str, str]], Coroutine[Any, Any, object]],
        None
    ]:
        # The return type may look a little weird, but this is how
        # @asynccontextmanager works. You pass it a function that returns an
        # async generator (which yields what the asynchronous context manager
        # then returns).
        yield self.update


async def main():
    async with APIClient(
        NoOpRatelimiter(),
        headers={'Authentication': f'Bot {TOKEN}'}
    ) as api:
        print(await api.fetch_my_user())


anyio.run(main)
```
