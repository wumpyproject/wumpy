from collections import deque
from contextlib import asynccontextmanager
from sys import platform
from typing import Any, AsyncGenerator, Dict, Literal, Optional, Tuple

import anyio
import anyio.abc
import anyio.streams.tls
from discord_gateway import DiscordConnection, CloseDiscordConnection, ConnectionRejected

from ..errors import ConnectionClosed

__all__ = ('IdentifyLock', 'DiscordGateway')


class IdentifyLock(anyio.Semaphore):
    """Simple lock that schedules releases after an amount of time."""

    def __init__(self, rate: int, per: int) -> None:
        super().__init__(per)

        self._rate = rate

    async def acquire(self) -> Literal[True]:
        """Acquire the lock, scheduling a release `rate` seconds later."""
        await super().acquire()

        asyncio.get_running_loop().call_later(self._rate, self.release)
        return True

    async def __aexit__(self, *_: Any) -> None:
        return  # We release the lock automatically


class DiscordGateway:
    """Default implementation of the Discord gateway.

    Behind the scenes this uses `discord-gateway` to handle the protocol.
    """

    def __init__(self, conn: DiscordConnection, sock: anyio.streams.tls.TLSStream) -> None:
        self._conn = conn
        self._sock = sock
        self._write_lock = anyio.Lock()

        self.events = deque()

    def __aiter__(self) -> 'DiscordGateway':
        return self

    @classmethod
    async def _connect_websocket(
        cls,
        uri: str,
        token: Optional[str] = None,
        intents: Optional[int] = None,
        *,
        conn: Optional[DiscordConnection] = None
    ) -> Tuple[DiscordConnection, anyio.streams.tls.TLSStream]:
        """Connect and completely initialize the connection to Discord.

        This method is also used when needing to reconnect after having
        disconnected.

        Parameters:
            uri: The URI to connect to.
            conn: The (potentially) old connection to reconnect.

        Raises:
            ConnectionRejected:
                Raised by discord_gateway if Discord rejects the connection.
        """
        if conn is None:
            conn = DiscordConnection(uri, encoding='json')
        else:
            # Reset the internal state of the connection to prepare for a new
            # WebSocket connection.
            conn.reconnect()

        sock = await anyio.connect_tcp(*conn.destination, tls=True)

        # Upgrade the connection to a WebSocket connection using a formatted
        # HTTP 1.1 request
        await sock.send(conn.connect())

        # Loop until we get the first HELLO event from Discord, we don't
        # want this event to be dispatched and we need to manually IDENTIFY
        # afterwards.
        event = None
        while event is None:
            try:
                for send in conn.receive(await sock.receive()):
                    await sock.send(send)
            except ConnectionRejected as err:
                raise ConnectionClosed('Discord rejected the WebSocket connection') from err
            except anyio.EndOfStream:
                # We haven't even received a HELLO event and sent a RESUME or
                # IDENTIFY command yet, odd.
                raise ConnectionClosed('Discord unexpectedly closed the socket')

            for event in conn.events():
                # This won't run at all if there are no events, what ends
                # up happening is that we let the code above communicate
                # until we get a complete HELLO event.
                break

        if conn.should_resume:
            await sock.send(conn.resume())
        else:
            await sock.send(conn.identify(
                token=token,
                intents=intents,
                properties={
                    '$os': platform,
                    '$browser': 'Wumpy',
                    '$device': 'Wumpy'
                },
            ))

        return conn, sock

    async def __anext__(self) -> Dict[str, Any]:
        while True:
            # The order here matters, first we want to check if there is an
            # event in the "buffer" so that we don't wait for data if we
            # already have it. The reason for this is because of the loop
            # necessary below, where multiple events can get added into this
            # "buffer" and cause desync issues.
            if self.events:
                return self.events.popleft()

            try:
                data = await self._sock.receive()
            except anyio.EndOfStream:
                # This should not happen, generally discord-gateway will raise
                # and we then respond to the closure. This error means that the
                # socket was closed without actually closing the WebSocket..
                # either way we can handle this normally

                # Hold the lock while reconnecting so that the heartbeater
                # doesn't attempt to heartbeat while this is happening
                async with self._write_lock:
                    await self._sock.aclose()

                    self._conn, self._sock = await self._connect_websocket(
                        self._conn.uri, conn=self._conn
                    )
                    # The data variable isn't defined so we can't run the code
                    # below, skip to the top of the loop and try again.
                    continue

            # The write lock is held during the entire sending and potential
            # reconnecting so that there isn't a race condition where the
            # heartbeater grabs the lock between sending and reconnecting.
            async with self._write_lock:
                try:
                    for send in self._conn.receive(data):
                        await self._sock.send(send)
                except CloseDiscordConnection as err:
                    # There are a few reasons why discord-gateway wants us to
                    # reconnect, either Discord sent an event telling us to do
                    # it or they didn't acknowledge a heartbeat

                    await self._sock.send(err.data)
                    await self._sock.aclose()

                    self._conn, self._sock = await self._connect_websocket(
                        self._conn.uri, conn=self._conn
                    )

            for event in self._conn.events():
                self.events.append(event)

    async def run_heartbeater(self):
        """Run the heartbeater periodically sending commands to Discord."""
        while True:
            # Attempt to acquire the write lock, this is held when reconnecting
            # so that there are no race conditions
            async with self._write_lock:
                await self._sock.send(self._conn.heartbeat())

            await anyio.sleep(self._conn.heartbeat_interval)

    @classmethod
    @asynccontextmanager
    async def connect(
        cls,
        uri: str,
        token: str,
        intents: int
    ) -> AsyncGenerator['DiscordGateway', None]:
        async with anyio.create_task_group() as tg:
            self = cls(*await cls._connect_websocket(uri, token, intents))
            tg.start_soon(self.run_heartbeater)

            yield self

            # For some reason we are now exiting the context manager
            # so we need to cancel the heartbeater or else it will block
            # forever since it is an infinite loop.
            tg.cancel_scope.cancel()
