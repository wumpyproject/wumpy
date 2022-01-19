import time
from contextlib import asynccontextmanager
from functools import partial
from typing import Any, AsyncContextManager, AsyncGenerator, Awaitable, Callable, Optional, Type
from types import TracebackType

import anyio
from discord_gateway import Opcode

__all__ = ('race', 'DefaultGatewayLimiter')


async def _done_callback(
    func: Callable[[], Awaitable[Any]],
    callback: Callable[[], Any]
) -> None:
    await func()

    # It is a deliberate design decision to not use a try/finally block here,
    # we only want to call the callback if func() was successful.
    callback()


async def race(*functions: Callable[[], Awaitable[Any]]) -> None:
    """Race several coroutine functions against each other.

    This function will return when the first of the functions complete, by
    cancelling all other functions. This means that only functions that can
    properly handle cancellation should be used with this function.

    Parameters:
        functions: The functions to race against each other.
    """
    if not functions:
        raise ValueError("race() missing at least 1 required positional argument")

    async with anyio.create_task_group() as tg:
        for func in functions:
            tg.start_soon(partial(_done_callback, func, tg.cancel_scope.cancel))


class DefaultGatewayLimiter:
    _lock: anyio.Lock
    _reset: Optional[float]
    _value: int

    RATE = 120 - 3  # We leave a margin of 3 heartbeats per minute
    PER = 60

    __slots__ = ('_lock', '_reset', '_value')

    def __init__(self) -> None:
        self._lock = anyio.Lock()

        self._reset = None
        self._value = self.RATE

    async def __aenter__(self) -> Callable[[Opcode], AsyncContextManager[None]]:
        return self.acquire

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        pass

    @asynccontextmanager
    async def acquire(self, opcode: Opcode) -> AsyncGenerator[None, None]:
        # Heartbeats are not
        if opcode is not Opcode.HEARTBEAT:
            async with self._lock:
                if self._reset is None or self._reset < time.perf_counter():
                    self._reset = time.perf_counter() + self.PER
                    self._value = self.RATE - 1

                elif self._value <= 0:
                    await anyio.sleep(self._reset - time.perf_counter())
                    self._reset = time.perf_counter() + self.PER
                    self._value = self.RATE - 1
                else:
                    self._value -= 1

        # Yield once we have released the lock, it is only held for the
        # case that we're sleeping, because if one tasks sleep then all
        # following tasks will also need to sleep.
        yield
