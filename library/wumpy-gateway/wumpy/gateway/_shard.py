import logging
import ssl
from collections import deque
from contextlib import AsyncExitStack
from datetime import datetime
from functools import partial
from random import random
from sys import platform
from types import TracebackType
from typing import (
    Any, Deque, Dict, List, Mapping, Optional, Tuple, Type, Union
)

import anyio
import anyio.abc
import anyio.lowlevel
import anyio.streams.tls
from discord_gateway import (
    CloseDiscordConnection, ConnectionRejected, DiscordConnection, Opcode,
    should_reconnect
)
from typing_extensions import Literal, Self

from ._errors import ConnectionClosed
from ._utils import DefaultGatewayLimiter, GatewayLimiter, race

__all__ = (
    'Shard',
)


_log = logging.getLogger(__name__)


_DISCONNECT_ERRS = (OSError, anyio.BrokenResourceError)


class Shard:
    """Simple implementation of the Discord gateway.

    To get started, instantiate a Shard instance and use it as an asynchronous
    context manager:

    ```python
    async with Shard('wss://gateway.discord.gg/', 'ABC.XYZ', 1) as conn:
        ...
    ```

    This way, the shard will ensure the connection is successfully closed once
    you're done. The shard also uses this opportunity to launch a task that
    indefinitely sends heartbeat commands and keeps the connection alive.

    The next part is to start receiving events - all you need to do is iterate
    through it as an asynchronous iterator:

    ```python
    async with Shard('wss://gateway.discord.gg/', 'ABC.XYZ', 1) as conn:
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
            async with Shard(...) as ws:
                async for event in ws:
                    await handle_event(event)

        asyncio.run(main)
        ```
    """

    _conn: DiscordConnection
    _sock: Optional[anyio.streams.tls.TLSStream]
    _ssl: Optional[ssl.SSLContext]

    _write_lock: anyio.Lock
    _reconnecting: anyio.Event
    _closed: anyio.Event
    _exit_stack: AsyncExitStack

    _events: Deque[Dict[str, Any]]

    token: str
    intents: int

    shard_id: Optional[Tuple[int, int]]
    max_concurrency: int

    _ratelimiter: GatewayLimiter

    __slots__ = (
        '_conn', '_sock', '_ssl', '_write_lock', '_reconnecting', '_closed', '_exit_stack',
        'token', 'intents', '_events', 'shard_id', 'max_concurrency', '_ratelimiter'
    )

    def __init__(
        self,
        uri: str,
        token: str,
        intents: int,
        shard_id: Optional[Tuple[int, int]] = None,
        *,
        session_id: Optional[str] = None,
        sequence: Optional[int] = None,
        max_concurrency: int = 1,
        encoding: Literal['json', 'etf'] = 'json',
        ratelimiter: Optional[GatewayLimiter] = None,
        ssl_context: Optional[ssl.SSLContext] = None
    ) -> None:
        self._conn = DiscordConnection(
            uri, session_id=session_id, sequence=sequence,
            encoding=encoding, compress='zlib-stream'
        )

        self._sock = None
        self._ssl = ssl_context

        # _write_lock, _reconnecting, _closed are all created in __aenter__()
        # because the event loop needs to be running when they are created
        self._exit_stack = AsyncExitStack()

        self.token = token
        self.intents = intents

        self._events = deque()

        self.shard_id = shard_id
        self.max_concurrency = max_concurrency

        self._ratelimiter = ratelimiter or DefaultGatewayLimiter()

    async def __aenter__(self) -> Self:
        _log.info('Entered the context manager (connecting to the gateway).')

        if hasattr(self, '_closed') and not self._closed.is_set():
            raise RuntimeError('Cannot connect shard multiple times')

        self._closed = anyio.Event()

        # Although this isn't meant to be used to wait until the gateway
        # is entered again, it is a good idea to play nicely and set this
        # event when we're initially connecting. Therefore, we don't overwrite
        # this attribute to allow _reconnect() to set the event.
        if not hasattr(self, '_reconnecting'):
            self._reconnecting = anyio.Event()

        self._write_lock = anyio.Lock()

        try:
            await self._exit_stack.enter_async_context(self._ratelimiter)

            await self._reconnect(reset=False)

            tg = await self._exit_stack.enter_async_context(anyio.create_task_group())
            tg.start_soon(self._run_heartbeater)
            return self
        except BaseException:
            await self._exit_stack.aclose()
            raise

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        # If there is an exception it will propagate and there is no need for
        # us to warn or error about it.
        _log.info('Exiting the context manager (closing the connection).')

        # If this was cancelled, or some other error occured, the
        # heartbeater will be cancelled either way meaning that
        # there is no point for a try/finally block here (since the
        # point of it is to cause the heartbeater to gracefully
        # exit).
        self._closed.set()

        try:
            # If we were cancelled this will raise a CancelledError - but we
            # still need to cleanup the socket.
            await self._exit_stack.__aexit__(exc_type, exc_val, traceback)
        finally:
            await self._aclose()

    def __aiter__(self) -> 'Shard':
        return self

    async def __anext__(self) -> Dict[str, Any]:
        return await self.receive_event()

    @property
    def session_id(self) -> str:
        """Session ID used to `RESUME` the connection."""
        if self._conn.session_id is None:
            raise RuntimeError('Cannot retrieve session ID without being connected')

        return self._conn.session_id

    @property
    async def sequence(self) -> int:
        """Heartbeat sequnce used together with the session ID."""
        if self._conn.sequence is None:
            raise RuntimeError('Cannot retrieve sequence without being connected')

        return self._conn.sequence

    @property
    def latency(self) -> float:
        """Rolling average latency to receiving an heartbeat ACK."""
        return self._conn.latency

    async def receive_event(self) -> Dict[str, Any]:
        """Receive the next event, waiting if there is none.

        This method contains almost all of the active logic that takes care
        of the WebSocket protocol and reconnecting when necessary.

        Returns:
            The full payload received from Discord.
        """
        if self._sock is None:
            raise RuntimeError('Cannot receive events from an unopened socket')

        while True:
            # The order here matters, first we want to check if there is an
            # event in the "buffer" so that we don't wait for data if we
            # already have it. The reason for this is because of the loop
            # necessary below, where multiple events can get added into this
            # "buffer" and cause desync issues.
            if self._events:
                # This codepath doesn't yield to the event loop, which is
                # generally bad practice. That said, it makes it harder to
                # catch up if the task is running behind. Therefore, we don't
                # checkpoint here either way.
                return self._events.popleft()

            try:
                data = await self._sock.receive()
            except (*_DISCONNECT_ERRS, anyio.EndOfStream):
                # This should not happen, generally discord-gateway will raise
                # and we then respond to the closure. This error means that
                # something went wrong with the socket we weren't expecting.
                _log.warning(
                    'Discord closed the socket without closing the WebSocket;'
                    ' reconnecting to the gateway.'
                )

                # Hold the lock while reconnecting so that the heartbeater
                # doesn't attempt to heartbeat while this is happening
                async with self._write_lock:
                    try:
                        for send in self._conn.receive(None):
                            await self._sock.send(send)
                    except _DISCONNECT_ERRS:
                        pass
                    except CloseDiscordConnection as err:
                        if err.data is not None:
                            try:
                                await self._sock.send(err.data)
                            except _DISCONNECT_ERRS:
                                pass

                        if not should_reconnect(err.code):
                            raise ConnectionClosed(
                                f'Discord closed the connection with code {err.code}'
                                f': {err.reason}' if err.reason else ''
                            )

                    await self._reconnect()

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
                except _DISCONNECT_ERRS:
                    _log.warning(
                        'Failed to respond to data received by Discord;'
                        ' reconnecting to the gateway.'
                    )

                    try:
                        for send in self._conn.receive(None):
                            await self._sock.send(send)
                    except _DISCONNECT_ERRS:
                        pass

                    await self._reconnect()

                except CloseDiscordConnection as err:
                    # There are a few reasons why discord-gateway wants us to
                    # reconnect, either Discord sent an event telling us to do
                    # it or they didn't acknowledge a heartbeat
                    _log.info('Closed the WebSocket; reconnecting to the gateway.')

                    try:
                        if err.data is not None:
                            await self._sock.send(err.data)
                    except _DISCONNECT_ERRS:
                        pass

                    if not should_reconnect(err.code):
                        raise ConnectionClosed(
                            f'Discord closed the WebSocket with code {err.code}'
                            f': {err.reason}' if err.reason else ''
                        )

                    await self._reconnect()

            for event in self._conn.events():
                self._events.append(event)

    async def _receive_hello(self) -> Optional[Dict[str, Any]]:
        if self._sock is None:
            raise RuntimeError('Cannot receive a HELLO event from a closed socket')

        event = None
        while event is None:
            try:
                for send in self._conn.receive(await self._sock.receive()):
                    await self._sock.send(send)
            except (*_DISCONNECT_ERRS, anyio.EndOfStream):
                _log.warning(
                    'Receiving the HELLO event failed with a general OSError or the socket'
                    ' closed; reconnecting to the gateway.'
                )
                try:
                    for send in self._conn.receive(None):
                        await self._sock.send(send)
                except _DISCONNECT_ERRS:
                    pass

                return None
            except CloseDiscordConnection as err:
                if err.data is not None:
                    try:
                        await self._sock.send(err.data)
                    except _DISCONNECT_ERRS:
                        pass

                if not should_reconnect(err.code):
                    raise ConnectionClosed(
                        f'Discord closed the WebSocket with code {err.code}'
                        f': {err.reason}' if err.reason else ''
                    )
                else:
                    # Since we didn't raise an Exception we should log this
                    # unexpected close code.
                    _log.warning(
                        f'Discord unexpectedly closed the WebSocket with code {err.code}'
                        f': {err.reason}' if err.reason else ''
                        '; reconnecting to the gateway.'
                    )

                return None
            except ConnectionRejected as err:
                raise ConnectionClosed('Discord rejected the WebSocket connection') from err

            for event in self._conn.events():
                # This won't run at all if there are no events, what ends
                # up happening is that we let the code above communicate
                # until we get a complete HELLO event.
                break

        return event

    async def _reconnect(self, *, reset: bool = True) -> None:
        while True:
            # If there is an existing socket, or we are making another attempt
            # from below, close it.
            if self._sock is not None:
                try:
                    await self._sock.aclose()
                except _DISCONNECT_ERRS:
                    pass

            if reset:
                # Reset the internal state of the connection to prepare for a new
                # WebSocket connection. This will exponentially backoff until it
                # receives a READY event.
                delay = self._conn.reconnect()
                _log.debug(f'Exponentially backing off reconnecting ({delay}s)')
                await anyio.sleep(delay)

            # In case this code loops, we are actually reconnecting and not
            # just connecting for the first time. The second iteration we
            # '*want* to back off.
            reset = True

            try:
                self._sock = await anyio.connect_tcp(
                    *self._conn.destination, tls=True,
                    # HTTP connections (which a WebSocket relies on) don't
                    # usually perform the closing TLS handshake
                    tls_standard_compatible=False, ssl_context=self._ssl
                )
            except _DISCONNECT_ERRS:
                # SSLError is a subclass of OSError so we can just directly
                # use OSError since it can also be raised by connect_tcp().
                _log.warning(
                    'Failed to open a TCP connection to Discord;'
                    ' reconnecting to the gateway.'
                )
                continue

            # Upgrade the connection to a WebSocket connection using a
            # formatted HTTP 1.1 request
            try:
                await self._sock.send(self._conn.connect())
            except _DISCONNECT_ERRS:
                _log.warning(
                    'Failed to send HTTP/1.1 opening request; reconnecting to the gateway.'
                )
                continue

            # Receive the HELLO event from Discord. If it failed for whatever
            # reason it'll close the WebSocket and return None.
            if await self._receive_hello() is None:
                # Logging for this failure is done within the method.
                continue

            try:
                if self._conn.should_resume:
                    async with self._ratelimiter(Opcode.RESUME):
                        await self._sock.send(self._conn.resume(self.token))

                    # If we RESUME, we should reset the cache of events because
                    # they will be sent again - although a reconnection should
                    # only really trigger within receive_event() when the
                    # events cache is already empty.
                    self._events = deque()

                else:
                    async with self._ratelimiter(Opcode.IDENTIFY):
                        await self._sock.send(self._conn.identify(
                            token=self.token,
                            intents=self.intents,
                            properties={
                                '$os': platform,
                                '$browser': 'Wumpy',
                                '$device': 'Wumpy'
                            },
                            shard=self.shard_id
                        ))
            except _DISCONNECT_ERRS:
                _log.warning(
                    'Failed to RESUME/IDENTIFY to the new connection because of an OSError;'
                    ' reconnecting to the gateway.'
                )

                try:
                    for send in self._conn.receive(None):
                        await self._sock.send(send)
                except _DISCONNECT_ERRS:
                    pass

                continue
            break

        self._reconnecting.set()
        self._reconnecting = anyio.Event()

    async def _aclose(self) -> None:
        # In case the event hasn't been set yet (it *should* be, but redundancy
        # with these types of things are good).
        self._closed.set()

        if self._sock is None:
            return

        try:
            async with self._write_lock:
                if self._conn.closing:
                    # If we're already closing/fully closed, or something went
                    # wrong while trying to close down the WebSocket it's best
                    # to return and only call 'await self._sock.aclose()'.
                    return

                try:
                    await self._sock.send(self._conn.close())
                except _DISCONNECT_ERRS:
                    _log.warning(
                        'Failed to send WebSocket close message over TCP connection;'
                        ' closing the connection as usual.'
                    )
                    return  # Move to the finally-clause

                try:
                    while True:
                        # Receive the acknowledgement of the closing per the
                        # WebSocket protocol
                        for data in self._conn.receive(await self._sock.receive()):
                            await self._sock.send(data)
                except (*_DISCONNECT_ERRS, anyio.EndOfStream):
                    # According to the WebSocket protocol we should've gotten a
                    # closing frame but it's not a big deal - we're closing the
                    # socket either way. Just close the socket as usual in the
                    # 'finally' block below.
                    _log.debug(
                        'Discord unexpectedly closed the socket before finishing the WebSocket'
                        ' closing handshake. Closing the TCP connection as usual.'
                    )
                except CloseDiscordConnection as err:
                    if err.data is not None:
                        try:
                            await self._sock.send(err.data)
                        except _DISCONNECT_ERRS:
                            pass
        finally:
            # No matter what happened - whether we completed the closing
            # handshake or was potentially cancelled (perhaps even before we
            # acquired the lock) - clean up the socket correctly.
            await self._sock.aclose()

    async def _run_heartbeater(self) -> None:
        if self._sock is None:
            raise RuntimeError('Cannot run heartbeater before connecting')
        if self._conn.heartbeat_interval is None:
            raise RuntimeError('Heartbeater started before connected')

        interval = self._conn.heartbeat_interval

        while True:
            if self._conn.closing:
                _log.debug(
                    'WebSocket in the middle of closing when attempting to heartbeat,'
                    ' waiting for reconnection event to be set.'
                )
                await self._reconnecting.wait()

                # Since we have reconnected, we should apply some jitter
                # to the next sleep so that not all bots which reconnect
                # send their heartbeats at the same time (causing strain
                # and worsens downtimes).
                interval = self._conn.heartbeat_interval * random()

            # Attempt to acquire the write lock, this is held when reconnecting
            # so that there are no race conditions
            async with self._write_lock:
                async with self._ratelimiter(Opcode.HEARTBEAT):
                    if self._conn.closing:
                        # Even though we may not be reconnecting or sending
                        # anything over the socket, a closure could have
                        # started while we were acquiring the lock or waiting
                        # on the ratelimiter. We cannot hold the lock while
                        # waiting on self._reconnecting because that would
                        # result in a dead-lock (since the lock is acquired
                        # to reconnect and set the event).
                        continue

                    _log.debug('Sending HEARTBEAT command over gateway.')
                    await self._sock.send(self._conn.heartbeat())

            # Wait for the first one to complete - either the expected sleeping
            # or during shutdown the _closed event.
            await race(partial(anyio.sleep, interval), self._closed.wait)

            interval = self._conn.heartbeat_interval  # Reset value after sleep

            if self._closed.is_set():
                _log.info('Close event is set - exiting heartbeater.')
                return

    async def request_guild_members(
        self,
        guild: Union[str, int],
        *,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        presences: Optional[bool] = None,
        users: Optional[Union[List[Union[str, int]], Union[str, int]]] = None,
        nonce: Optional[str] = None
    ) -> None:
        """Request guild member information from Discord.

        The response to this command will be received by a DISPATCH event
        asynchronously. Use `nonce` to keep track of which call corresponds
        to which response.

        Parameters:
            guild: The guild to get the information from.
            limit: The maximum amount of members to send.
            presences: Whether to send presences for the members.
            users: List of specific users to request member data for.
            nonce: A helpful nonce value to identify a specific response.
        """
        if self._sock is None:
            raise RuntimeError('Cannot request guild members before connecting')

        async with self._write_lock:
            async with self._ratelimiter(Opcode.REQUEST_GUILD_MEMBERS):
                await self._sock.send(self._conn.request_guild_members(
                    guild=guild, limit=limit, query=query, presences=presences,
                    users=users, nonce=nonce
                ))

    async def update_presence(
        self,
        *,
        activities: List[Mapping[str, Any]],
        status: Literal['online', 'dnd', 'idle', 'offline'] = 'online',
        afk: bool = False,
        since: Optional[Union[int, datetime]] = None,
    ) -> None:
        """Update the presence of the bot in the guilds this shard handles.

        Parameters:
            activities: A list of activities the bot is doing.
            status: The new status icon of the bot.
            afk: Whether or not the bot should be treated as AFK.
            since: The time that the bot went idle (in milliseconds).
        """
        if self._sock is None:
            raise RuntimeError('Cannot update presence before connecting')

        if isinstance(since, datetime):
            since = int(since.timestamp() * 1000)

        async with self._write_lock:
            async with self._ratelimiter(Opcode.PRESENCE_UPDATE):
                await self._sock.send(self._conn.update_presence(
                    activities=activities, status=status, afk=afk, since=since
                ))

    async def update_voice_state(
        self,
        guild: Union[str, int],
        channel: Optional[Union[str, int]],
        *,
        mute: bool = False,
        deafen: bool = False
    ) -> None:
        """Update the voice state of a specific guild.

        `wumpy-gateway` does not currently support voice connections. This is
        implemented so that you can build voice-support off of this.

        Parameters:
            guild: The guild to update the voice state for.
            channel: The voice channel to move the bot to.
            mute: Whether or not the bot should be muted.
            deafen: Whether or not the bot should be deafened.
        """
        if self._sock is None:
            raise RuntimeError('Cannot update voice state before connecting')

        async with self._write_lock:
            async with self._ratelimiter(Opcode.VOICE_STATE_UPDATE):
                await self._sock.send(self._conn.update_voice_state(
                    guild, channel, mute=mute, deafen=deafen
                ))
