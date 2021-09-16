"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
from typing import (
    Any, Awaitable, Callable, Dict, Optional, Tuple, overload
)

import anyio
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from ..utils import MISSING
from .base import (
    CommandInteraction, InteractionType,
    MessageComponentInteraction
)
from .commands.registrar import CommandRegistrar
from .components.handler import ComponentHandler
from .rest import InteractionRequester


class InteractionApp(CommandRegistrar, ComponentHandler):
    """Simple interaction application implementing the ASGI protocol.

    This is a very bare implementation of the ASGI protocol that only does
    what's absolutely necessary for the Discord API.
    """

    rest: InteractionRequester
    verification: VerifyKey

    token: str
    secret: str

    @overload
    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        token: str = MISSING
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        secret: str = MISSING
    ) -> None:
        ...

    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        token: str = MISSING,
        secret: str = MISSING
    ) -> None:
        if token is MISSING and secret is MISSING:
            raise TypeError("one of 'token' and 'secret' is required")

        super().__init__()

        self.rest = InteractionRequester(application_id)
        self.verification = VerifyKey(bytes.fromhex(public_key))

        self.token = token
        self.secret = secret

    async def process_interaction(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        data: Dict[str, Any]
    ) -> None:
        """Process the interaction and trigger appropriate callbacks."""
        # This event is necessary as we should not return to the ASGI server
        # before send has been called, we later wait for this event.
        complete = anyio.Event()

        def wrapped(data: Dict[str, Any]) -> Awaitable[None]:
            complete.set()  # Set the event and signal a response has been sent
            return send(data)

        async with anyio.create_task_group() as tg:
            enum_val = InteractionType(data['type'])
            if enum_val is InteractionType.application_command:
                self.handle_command(
                    CommandInteraction(self, send, self.rest, data),
                    tg=tg
                )
            elif enum_val is InteractionType.message_component:
                self.handle_component(
                    MessageComponentInteraction(self, send, self.rest, data),
                    tg=tg
                )

            with anyio.fail_after(3):
                await complete.wait()

    async def verify_request(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]]
    ) -> Tuple[bool, Optional[bytes]]:
        """Verify that the request came from Discord.

        The first item in the tuple is a bool indicating whether the request
        came from Discord, the second is the body received which may be None
        when the former is False.
        """
        signature: Optional[bytes] = None
        timestamp: Optional[bytes] = None

        for header, value in scope['headers']:
            if header == b'content-type' and value != b'application/json':
                # We can only handle application/json requests
                return False, None

            if header == b'x-signature-timestamp':
                timestamp = value
            elif header == b'x-signature-ed25519':
                signature = value

        if signature is None or timestamp is None:
            return False, None

        body = bytearray()
        # Initialize a fake request to make the while loop work
        request: Dict[str, Any] = {'more_body': True}
        while request['more_body']:
            request = await receive()
            body.extend(request['body'])

        try:
            self.verification.verify(timestamp + bytes(body), bytes.fromhex(signature.decode()))
        except BadSignatureError:
            # This request was not sent by Discord
            return False, body

        return True, body

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        # The only endpoint we have is POST /
        if scope['path'] != '/':
            await send({
                'type': 'http.response.start', 'status': 404,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Not Found'})
            return

        elif scope['method'] != 'POST':
            await send({
                'type': 'http.response.start', 'status': 405,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Method Not Allowed'})
            return

        verified, body = await self.verify_request(scope, receive)

        # The latter is for static type checkers, even though there is no case
        # were verified is True and body is None
        if not verified or body is None:
            await send({
                'type': 'http.response.start', 'status': 401,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Unauthorized'})
            return

        data = json.loads(body)

        if data['type'] == 1:  # PING
            await send({
                'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'application/json')]
            })
            await send({'type': 'http.response.body', 'body': b'{"type": 1}'})
            return

        await self.process_interaction(send, data)
