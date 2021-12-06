from collections import deque
from contextlib import asynccontextmanager
from sys import platform
from typing import Any, AsyncGenerator, Dict, NoReturn, Optional, Tuple

import anyio
import anyio.abc
import anyio.lowlevel
import anyio.streams.tls
from discord_gateway import (
    CloseDiscordConnection, ConnectionRejected, DiscordConnection
)

from .errors import ConnectionClosed

__all__ = ('Shard',)


class Shard:
    """Simple implementation of the Discord gateway.

    To get started, use the `connect()` classmethod in an asynchronous
    context manager - passing the URI, token and intents to connect with:

    ```python
    async with Shard.connect('wss://gateway.discord.gg/', 'ABC.XYZ', 1) as conn:
        ...
    ```

    This way, the shard will ensure the connection is successfully closed once
    you're done. The shard also uses this opportunity to launch a task that
    indefinitely sends heartbeat commands and keeps the connection alive.

    The next part is to start receiving events, this is done using the
    instance that `Shard.connect()` yields. All you have to do is iterate
    through it:

    ```python
    async with Shard.connect('wss://gateway.discord.gg/', 'ABC.XYZ', 1) as conn:
        async for event in conn:
            ...
    ```

    This is an endless loop that should never terminate because
    reconnecting and keeping the connection alive is all handled. `event` is
    the deserialized JSON that Discord sent over the gateway.

    Examples:

        ```python
        import asyncio

        from wumpy.gateway import Shard

        async def handle_event(payload):
            print(f"Received {payload['t']}:", payload['d'])

        async def main():
            # Replace the ... with the uri, token and intents to use
            async with Shard.connect(...) as ws:
                async for event in ws:
                    await handle_event(event)

        asyncio.run(main)
        ```
    """

    events: deque

    def __init__(
        self,
        conn: DiscordConnection,
        sock: anyio.streams.tls.TLSStream,
        token: str,
        intents: int
    ) -> None:
        self._conn = conn
        self._sock = sock

        self.token = token
        self.intents = intents

        self.events = deque()

    def __aiter__(self) -> 'Shard':
        return self

    @classmethod
    @asynccontextmanager
    async def connect(
        cls,
        uri: str,
        token: str,
        intents: int
    ) -> AsyncGenerator['Shard', None]:
        """Connect and initialize the connection to Discord.

        This returns an asynchronous context manager that yields a connected
        shard instance and will correctly close and cleanup the connection
        when exiting.

        This method also takes the opportunity to start a task that sends
        heartbeat commands which keep the connection alive.
        """
        async with anyio.create_task_group() as tg:
            self = cls(*await cls.create_connection(uri, token, intents), token, intents)
            tg.start_soon(self.run_heartbeater)

            try:
                yield self
            finally:
                # We used to cancel the heartbeater before closing the
                # WebSocket to prevent race conditions between sending a
                # heartbeat command and actually closing the socket.
                # This was fixed when discord-gateway added the 'closing'
                # property because now the heartbeater will wait when this is
                # True - which it is as soon as the closing handshake has
                # started (making it safe).
                # Cancelling the cancel-scope we're in and then immediately
                # trying to gracefully close the socket also meant we
                # cancelled the actual closing too unecessarily *facepalm*.
                await self.aclose()

                # Task groups exit when all tasks have completed, the
                # heartbeater is an endless loop so we need to cancel it to
                # be able to exit..
                tg.cancel_scope.cancel()

    @classmethod
    async def create_connection(
        cls,
        uri: str,
        token: str,
        intents: int,
        *,
        conn: Optional[DiscordConnection] = None
    ) -> Tuple[DiscordConnection, anyio.streams.tls.TLSStream]:
        """Create and initialize the connection to Discord.

        Consider using the shorthand `connect()` classmethod before looking at
        this method.

        This is used to (re)create the underlying socket and protocol
        implementation, returning them in a tuple possible to unpack into
        `__init__()` with the token and intents again.

        Parameters:
            uri: The URI to connect to.
            token: The token to identify with.
            intents: Intents to identify with.
            conn: The (potentially) old connection to reconnect.

        Raises:
            ConnectionClosed:
                Discord rejected or unexpectedly closed the underlying socket.
        """
        if conn is None:
            conn = DiscordConnection(uri, encoding='json', compress='zlib-stream')
        else:
            # Reset the internal state of the connection to prepare for a new
            # WebSocket connection.
            conn.reconnect()

        sock = await anyio.connect_tcp(
            *conn.destination, tls=True,
            # HTTP connections (which a WebSocket relies on) don't usually
            # perform the closing TLS handshake
            tls_standard_compatible=False
        )
        try:
            # Upgrade the connection to a WebSocket connection using a
            # formatted HTTP 1.1 request
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
                    raise ConnectionClosed(
                        'Discord rejected the WebSocket connection'
                    ) from err
                except anyio.EndOfStream:
                    # We haven't even received a HELLO event and sent a RESUME
                    # or IDENTIFY command yet, odd.
                    raise ConnectionClosed('Discord unexpectedly closed the socket')

                for event in conn.events():
                    # This won't run at all if there are no events, what ends
                    # up happening is that we let the code above communicate
                    # until we get a complete HELLO event.
                    break

            if conn.should_resume:
                await sock.send(conn.resume(token))
            else:
                await sock.send(conn.identify(
                    token=token,
                    intents=intents,
                    properties={
                        '$os': platform,
                        '$browser': 'Wumpy',
                        '$device': 'Wumpy'
                    },
                    presence={
                        'activities': [],
                        'status': 'offline',
                        'afk': True
                    }
                ))
        except:
            # The bare except is on purpose, we want to catch *any* error that
            # happened including cancellation errors.
            await sock.aclose()
            raise

        return conn, sock

    async def __anext__(self) -> Dict[str, Any]:
        """Receive the next event, waiting if there is none.

        This method contains almost all of the active logic that takes care
        of the WebSocket protocol and reconnecting when necessary.

        If used directly, it is important to close the socket if the task is
        cancelled. This is designed to sit under the `connect()` classmethod
        which handles cancellation.

        Returns:
            The full payload received from Discord.
        """
        while True:
            # The order here matters, first we want to check if there is an
            # event in the "buffer" so that we don't wait for data if we
            # already have it. The reason for this is because of the loop
            # necessary below, where multiple events can get added into this
            # "buffer" and cause desync issues.
            if self.events:
                event = self.events.popleft()

                # Normally this codepath wouldn't yield to the event loop
                # because we don't await anything, this is confusing from the
                # user's perspective and in general considered bad design.
                await anyio.lowlevel.checkpoint()

                # We popped the event before yielding, otherwise it may have
                # been popped by another task.
                return event

            try:
                data = await self._sock.receive()
            except anyio.EndOfStream:
                # This should not happen, generally discord-gateway will raise
                # and we then respond to the closure. This error means that the
                # socket was closed without actually closing the WebSocket..
                # either way we can handle this normally

                # Note: The heartbeater uses the 'closing' property on
                # self._conn so that there are no race conditions.
                for send in self._conn.receive(None):
                    await self._sock.send(send)

                await self._sock.aclose()

                self._conn, self._sock = await self.create_connection(
                    self._conn.uri, self.token, self.intents,
                    conn=self._conn
                )
                # The data variable isn't defined so we can't run the code
                # below, skip to the top of the loop and try again.
                continue

            try:
                for send in self._conn.receive(data):
                    await self._sock.send(send)
            except CloseDiscordConnection as err:
                # There are a few reasons why discord-gateway wants us to
                # reconnect, either Discord sent an event telling us to do
                # it or they didn't acknowledge a heartbeat.

                # Same as above, this is safe from race conditions because
                # of the 'closing' property on self._conn.
                if err.data is not None:
                    await self._sock.send(err.data)

                await self._sock.aclose()

                self._conn, self._sock = await self.create_connection(
                    self._conn.uri, self.token, self.intents,
                    conn=self._conn
                )

            for event in self._conn.events():
                self.events.append(event)

    async def aclose(self) -> None:
        """Close and cleanup the connection to Discord.

        As with most methods this is automatically called with `connect()` and
        should generally not be used directly.

        This is safe to called in a `finally` block - even when cancelled - and
        will correctly cleanup the underlying socket.
        """
        try:
            await self._sock.send(self._conn.close())

            try:
                while True:
                    # Receive the acknowledgement of the closing per the
                    # WebSocket protocol
                    for data in self._conn.receive(await self._sock.receive()):
                        await self._sock.send(data)
            except anyio.EndOfStream:
                # According to the WebSocket protocol we should've gotten a
                # closing frame but it's not a big deal - we're closing the
                # socket either way. Just close the socket as usual in the
                # 'finally' block below.
                pass
            except CloseDiscordConnection as err:
                if err.data is not None:
                    await self._sock.send(err.data)
        finally:
            # No matter what happened - whether we completed the closing
            # handshake or was potentially cancelled - clean up the socket
            # correctly. If we were cancelled (and are running under Trio)
            # this will also be cancelled and cause the socket to forcefully
            # close, the end result is the same.
            await self._sock.aclose()

    async def run_heartbeater(self) -> NoReturn:
        """Run the heartbeater periodically sending commands to Discord.

        This method is automatically started as a task by the `connect()`
        classmethod in the asynchronous context manager so there is not much of
        a need to use this directly.

        Raises:
            RuntimeError: This method is called before being connected.

        Returns:
            This method is meant to never run and loops infinitely, it is only
            stopped by being cancelled.
        """
        if self._conn.heartbeat_interval is None:
            raise RuntimeError('Heartbeater started before connected')

        while True:
            # This property is set to True if the WebSocket is at any stage of
            # its closing handshake, meaning that when this is False the
            # WebSocket is reconnecting (or potentially closing for good).
            # Paired with the fact that self._sock and self._conn are only
            # ever overwritten after having sent an IDENTIFY or RESUME command,
            # this simple if-statement guards all potential race conditions
            # from happening with the socket.
            if not self._conn.closing:
                await self._sock.send(self._conn.heartbeat())

            await anyio.sleep(self._conn.heartbeat_interval)
