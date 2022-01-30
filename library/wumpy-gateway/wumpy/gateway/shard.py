import logging
from collections import deque
from contextlib import asynccontextmanager
from functools import partial
from sys import platform
from typing import (
    Any, AsyncContextManager, AsyncGenerator, Callable, Deque, Dict, Optional,
    Tuple
)

import anyio
import anyio.abc
import anyio.lowlevel
import anyio.streams.tls
from discord_gateway import (
    CloseDiscordConnection, ConnectionRejected, DiscordConnection, Opcode,
    should_reconnect
)

from .errors import ConnectionClosed
from .utils import DefaultGatewayLimiter, race

__all__ = ('Shard',)


_log = logging.getLogger(__name__)


GatewayLimiter = Callable[[Opcode], AsyncContextManager[None]]


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

    _conn: DiscordConnection
    _sock: anyio.streams.tls.TLSStream
    _write_lock: anyio.Lock
    _closed: anyio.Event

    token: str
    intents: int

    events: Deque[Dict[str, Any]]

    ratelimiter: GatewayLimiter

    __slots__ = (
        '_conn', '_sock', '_write_lock', '_closed', 'token', 'intents',
        'events', 'ratelimiter'
    )

    def __init__(
        self,
        conn: DiscordConnection,
        sock: anyio.streams.tls.TLSStream,
        token: str,
        intents: int,
        ratelimiter: GatewayLimiter,
    ) -> None:
        self._conn = conn
        self._sock = sock

        self._write_lock = anyio.Lock()
        self._closed = anyio.Event()

        self.token = token
        self.intents = intents

        self.events = deque()

        self.ratelimiter = ratelimiter

    def __aiter__(self) -> 'Shard':
        return self

    @classmethod
    @asynccontextmanager
    async def connect(
        cls,
        uri: str,
        token: str,
        intents: int,
        ratelimiter: Optional[AsyncContextManager[GatewayLimiter]] = None,
    ) -> AsyncGenerator['Shard', None]:
        """Connect and initialize the connection to Discord.

        This returns an asynchronous context manager that yields a connected
        shard instance and will correctly close and cleanup the connection
        when exiting.

        This method also takes the opportunity to start a task that sends
        heartbeat commands which keep the connection alive.

        Parameters:
            uri: The WebSocket URI to connect to.
            token: The token to IDENTIFY with.
            intents: The intents to use when IDENTIFYing.
            ratelimiter:
                An asynchronous context manager that will be entered and should
                return a callable, this callable will be called with the opcode
                that is about to be sent and should return a asynchronous
                context manager that will be entered before sending the command
                over the gateway.
        """
        async with (ratelimiter or DefaultGatewayLimiter()) as limiter:
            _log.info('Connecting to the Discord gateway...')
            self = cls(
                *await cls.create_connection(uri, token, intents, limiter=limiter),
                token, intents, limiter
            )
            _log.info('Successfully established connection to the Discord gateway.')

            try:
                async with anyio.create_task_group() as tg:
                    _log.info('Starting gateway heartbeat task.')
                    tg.start_soon(self.run_heartbeater)

                    yield self

                    # If this was cancelled, or some other error occured, the
                    # heartbeater will be cancelled either way meaning that there
                    # is no point for a try/finally block here (since the point of
                    # it is to cause the heartbeater to gracefully exit).
                    self._closed.set()

            finally:
                _log.info('Exiting the context manager - closing the connection.')
                await self.aclose()

    @classmethod
    async def create_connection(
        cls,
        uri: str,
        token: str,
        intents: int,
        *,
        limiter: GatewayLimiter,
        conn: Optional[DiscordConnection] = None,
    ) -> Tuple[DiscordConnection, anyio.streams.tls.TLSStream]:
        """Create and initialize the connection to Discord.

        Consider using the shorthand `connect()` classmethod before looking at
        this method.

        This is used to (re)create the underlying socket and protocol
        implementation, returning them in a tuple possible to unpack into
        `__init__()` with the token and intents again.

        This can be put in an infinite loop that catches `ConnectionClosed` as
        it uses the exponential backoff feature of `discord-gateway`.

        Parameters:
            uri: The URI to connect to.
            token: The token to identify with.
            intents: Intents to identify with.
            limiter: The ratelimiter for the IDENTIFY command to use.
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
            await anyio.sleep(conn.reconnect())

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
                async with limiter(Opcode.RESUME):
                    await sock.send(conn.resume(token))
            else:
                async with limiter(Opcode.IDENTIFY):
                    await sock.send(conn.identify(
                        token=token,
                        intents=intents,
                        properties={
                            '$os': platform,
                            '$browser': 'Wumpy',
                            '$device': 'Wumpy'
                        },
                    ))
        except:
            # We want to catch *any* error that happened including cancellation
            # errors so that we can cleanup.
            _log.critical('Failed to (re)connect to the Discord gateway.', exc_info=True)
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
                _log.warn(
                    'Discord closed the socket without closing the WebSocket; '
                    'reconnecting to the gateway.'
                )

                # Hold the lock while reconnecting so that the heartbeater
                # doesn't attempt to heartbeat while this is happening
                async with self._write_lock:
                    for send in self._conn.receive(None):
                        await self._sock.send(send)

                    await self._sock.aclose()

                    while True:
                        try:
                            self._conn, self._sock = await self.create_connection(
                                self._conn.uri, self.token, self.intents,
                                limiter=self.ratelimiter, conn=self._conn
                            )
                        except ConnectionClosed:
                            continue

                        break

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
                    _log.info('Closed the WebSocket, reconnecting to the gateway.')

                    if err.data is not None:
                        await self._sock.send(err.data)

                    await self._sock.aclose()

                    if not should_reconnect(err.code):
                        raise ConnectionClosed(
                            f'Discord closed the WebSocket with code {err.code}'
                            f': {err.reason}' if err.reason else ''
                        )

                    while True:
                        try:
                            self._conn, self._sock = await self.create_connection(
                                self._conn.uri, self.token, self.intents,
                                limiter=self.ratelimiter, conn=self._conn
                            )
                        except ConnectionClosed:
                            continue

                        break

            for event in self._conn.events():
                self.events.append(event)

    async def aclose(self) -> None:
        """Close and cleanup the connection to Discord.

        As with most methods this is automatically called with `connect()` and
        should generally not be used directly.

        This is safe to called in a `finally` block - even when cancelled - and
        will correctly cleanup the underlying socket.
        """
        # In case the event hasn't been set yet (such as if this is directly
        # called by the user for some reason).
        self._closed.set()

        try:
            async with self._write_lock:
                if self._conn.closing:
                    # If we're already closing/fully closed, or something went
                    # wrong while trying to close down the WebSocket it's best
                    # to return and only call 'await self._sock.aclose()'.
                    return

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
                    _log.warning(
                        'Discord unexpectedly closed the socket before '
                        'finishing the WebSocket closing handshake.'
                    )
                except CloseDiscordConnection as err:
                    if err.data is not None:
                        await self._sock.send(err.data)
        finally:
            # No matter what happened - whether we completed the closing
            # handshake or was potentially cancelled (perhaps even before we
            # acquired the lock) - clean up the socket correctly.
            await self._sock.aclose()

    async def run_heartbeater(self) -> None:
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
            # Attempt to acquire the write lock, this is held when reconnecting
            # so that there are no race conditions
            async with self._write_lock:

                # Even though we may not be reconnecting or sending anything
                # over the socket, a closure may have started that we haven't
                # completed yet. Just skip sending heartbeats in that case.
                if not self._conn.closing:
                    _log.debug('Sending HEARTBEAT command over gateway.')
                    async with self.ratelimiter(Opcode.HEARTBEAT):
                        await self._sock.send(self._conn.heartbeat())
                else:
                    _log.debug('Attempted to heartbeat while closing; skipping.')

            # Wait for the first one to complete - either the expected sleeping
            # or during shutdown the _closed event.
            await race(partial(anyio.sleep, self._conn.heartbeat_interval), self._closed.wait)

            if self._closed.is_set():
                _log.info('Close event is set - exiting heartbeater.')
                return
