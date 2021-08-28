import asyncio
import enum
import json
import zlib
from sys import platform
from typing import Any, Callable, Dict, Literal, Optional, SupportsInt

import aiohttp
from typing_extensions import Protocol

from ..errors import ConnectionClosed, ReconnectWebsocket

__all__ = ('IdentifyLock', 'Connection', 'Shard')


class ZlibDecompressor(Protocol):
    def __init__(self) -> None: ...

    def decompress(self, data: bytes, max_length=0) -> bytes: ...


class Opcode(enum.IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class IdentifyLock(asyncio.Semaphore):
    """Simple lock that schedules releases after an amount of time."""

    # There's no point in defining __slots__, asyncio doesn't

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


class Connection:
    """WebSocket connection to Discord."""

    token: str
    intents: int

    ws: Optional[aiohttp.ClientWebSocketResponse]
    heartbeater: Optional[asyncio.Task]

    decompressor: ZlibDecompressor
    identify_semaphore: Optional[asyncio.Semaphore]

    session_id: str
    heartbeat_interval: int
    sequence: int

    __slots__ = (
        'token', 'intents', 'ws', 'heartbeater', 'buffer',
        'decompressor', 'identify_lock', 'session_id', 'heartbeat_interval',
        'heartbeat_ack', 'sequence'
    )

    def __init__(
        self,
        token: str,
        intents: SupportsInt,
        identify_lock: IdentifyLock,
        *,
        zlib_decompressor: Callable[[], ZlibDecompressor] = zlib.decompressobj
    ) -> None:
        self.token = token
        self.intents = int(intents)

        self.ws = None
        self.heartbeater = None

        self.buffer = bytearray()
        self.decompressor = zlib_decompressor()
        self.identify_lock = identify_lock

        self.session_id = ''
        self.heartbeat_interval = -1
        self.heartbeat_ack = True
        self.sequence = 0

    async def send(self, data: Dict[str, Any]) -> None:
        """Send data to the Discord gateway, respecting rate limits."""
        if self.ws is None:
            raise RuntimeError("WebSocket not yet running")

        return await self.ws.send_json(data)

    async def receive(self, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait to receive a message from the WebSocket."""
        if self.ws is None:
            raise RuntimeError("WebSocket not yet running")

        while True:
            # Loop until we resolve a complete message
            msg = await self.ws.receive(timeout=timeout)
            if msg.type is aiohttp.WSMsgType.BINARY:
                self.buffer.extend(msg.data)

                # Check if this the end of the ZLIB event
                if len(msg.data) < 4 or msg.data[-4:] != b'\x00\x00\xff\xff':
                    continue

                data = self.decompressor.decompress(self.buffer)
                self.buffer = bytearray()
                return json.loads(data)

            elif msg.type is aiohttp.WSMsgType.TEXT:
                return json.loads(msg.data)

            elif msg.type is aiohttp.WSMsgType.ERROR:
                raise ConnectionClosed(
                    f"WebSocket closed with an error: {msg.data}"
                )

            else:
                # msg.type is CLOSE, CLOSING, or CLOSED
                raise ReconnectWebsocket(False)

    async def heartbeat(self) -> None:
        """Send a heartbeat to the Discord gateway."""
        await self.send({'op': Opcode.HEARTBEAT, 'd': self.sequence})
        self.sequence += 1

    async def start_heartbeating(self) -> None:
        """Start a loop sending heartbeat requests."""
        if not self.ws:
            raise RuntimeError("WebSocket not yet running")

        while True:
            if not self.heartbeat_ack:
                # Our last heartbeat wasn't acknowledged
                await self.ws.close(code=1006)  # Abnormal closure
                raise ReconnectWebsocket(True)

            await self.heartbeat()
            await asyncio.sleep(self.heartbeat_interval)

    async def identify(self, extra: Dict[str, Any] = {}) -> None:
        """Identify to the Discord gateway.

        `extra` is a dict that will be called with `dict.update()`.
        """
        if self.identify_lock is None:
            raise RuntimeError("'identify()' called before WebSocket was connected")

        async with self.identify_lock:
            data = {
                'token': self.token,
                'properties': {
                    '$os': platform,
                    '$browser': 'Wumpy',
                    '$device': 'Wumpy'
                },
                'intents': self.intents
            }
            data.update(extra)

            await self.send({'op': Opcode.IDENTIFY, 'd': data})

    async def resume(self) -> None:
        """Attempt to resume the connection to Discord.

        This will then cause the gateway to replay all the events missed since
        the last heartbeat exchanged and finish with a RESUMED opcode.
        """
        await self.send({
            'op': Opcode.RESUME,
            'd': {
                'token': self.token,
                'session_id': self.session_id,
                'seq': self.sequence
            }
        })

    async def connect(self, response: aiohttp.ClientWebSocketResponse) -> None:
        """Start the WebSocket and make the initial handshake.

        This consists of waiting for an HELLO opcode, starting the heartbeater
        and then sending an IDENTIFY request.
        """
        self.ws = response

        hello = await self.receive()

        if hello['op'] != Opcode.HELLO:
            raise RuntimeError(f"Expected opcode HELLO ({Opcode.HELLO}) received {hello}")

        # Discord sends the interval in ms
        self.heartbeat_interval = hello['d']['heartbeat_interval'] / 1000
        self.heartbeater = asyncio.get_running_loop().create_task(self.start_heartbeating())

        await self.identify()

    async def poll_gateway(self) -> Dict[str, Any]:
        """Poll the gateway for another event.

        This will wait up to 60 seconds per packet (in the case that the
        event is split over multiple).
        """
        if self.ws is None or self.heartbeater is None:
            raise RuntimeError("attempted to poll gateway before WebSocket started")

        try:
            while True:
                event = await self.receive(timeout=60)
                if event is None:
                    return event

                if event['op'] == Opcode.HEARTBEAT_ACK:
                    self.heartbeat_ack = True
                    continue

                elif event['op'] == Opcode.HEARTBEAT:
                    await self.heartbeat()
                    continue

                elif event['op'] == Opcode.DISPATCH and event['t'] == 'READY':
                    self.session_id = event['d']['session_id']
                    # No continue as we still want to return the event

                return event

        except asyncio.TimeoutError:
            # The receive() call timed out, this means that Discord did not
            # even send a HEARTBEAT_ACK within sufficient time. The Discord
            # documentation recommend terminating the connection, reconnecting
            # and sending a RESUME command.
            self.heartbeater.cancel()
            await self.ws.close(code=1006)  # Abnormal closure

            if self.ws.close_code in {1000, 4004, 4010, 4011, 4012, 4013, 4014}:
                raise ConnectionClosed(
                    f'WebSocket closed with error code {self.ws.close_code}'
                )

            raise ReconnectWebsocket(True)


class Shard(Connection):
    """Shard connection to the Discord gateway.

    This is not much different from a Connection, it just simply passes
    the necessary `shard` property when sending the IDENTIFY command.
    """

    def __init__(
        self,
        token: str,
        intents: SupportsInt,
        identify_lock: IdentifyLock,
        shard: int,
        num_shards: int,
        *,
        zlib_decompressor: Callable[[], ZlibDecompressor] = zlib.decompressobj
    ) -> None:
        super().__init__(token, intents, identify_lock, zlib_decompressor=zlib_decompressor)

        self.shard_id = [shard, num_shards]

    async def identify(self, extra: Dict[str, Any] = {}) -> None:
        data = {'shard': self.shard_id}
        data.update(extra)
        await super().identify(data)
