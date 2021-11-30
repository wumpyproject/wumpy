import json
from typing import (
    Any, Awaitable, Callable, Dict, List, Optional, Tuple, overload
)

import anyio
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from .base import CommandInteraction, ComponentInteraction, InteractionType
from .commands.registrar import CommandRegistrar
from .components.handler import ComponentHandler
from .rest import InteractionRequester

__all__ = ('InteractionApp',)


class InteractionApp(CommandRegistrar, ComponentHandler):
    """Simple interaction application implementing the ASGI protocol.

    This is a very bare implementation of the ASGI protocol that only does
    what's absolutely necessary for the Discord API.
    """

    rest: InteractionRequester
    verification: VerifyKey

    token: Optional[str]
    secret: Optional[str]

    @overload
    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        token: Optional[str] = None
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        secret: Optional[str] = None
    ) -> None:
        ...

    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        token: Optional[str] = None,
        secret: Optional[str] = None,
        register_commands: bool = True,
    ) -> None:
        super().__init__()

        self.rest = InteractionRequester(application_id)
        self.verification = VerifyKey(bytes.fromhex(public_key))

        self.token = token
        self.secret = secret

        self.rest = InteractionRequester(application_id, token=token, secret=secret)

        self.register_commands = register_commands

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
                    CommandInteraction(self, wrapped, self.rest, data),
                    tg=tg
                )
            elif enum_val is InteractionType.message_component:
                self.handle_component(
                    ComponentInteraction(self, wrapped, self.rest, data),
                    tg=tg
                )

            with anyio.fail_after(3):
                await complete.wait()

    async def verify_request(
        self,
        scope: Dict[str, Any],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        *,
        # These are actually here so that they can be modified, users can
        # subclass and call super() modifying these
        type: str = 'http',
        path: str = '/',
        method: str = 'POST',
    ) -> bool:
        """Verify that the request was made to the correct endpoint.

        Returning a bool indicating whether an error response has been sent.

        If another endpoint should be used, this should be overwritten and
        call super() with the new values:

        ```python
        class MyApp(InteractionApp):
            async def verify_request(self, *args):
                return await super().verify_request(*args, path='/interactions')
        ```
        """
        if scope['type'] != type:
            await send({
                'type': 'http.response.start', 'status': 501,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Not Implemented'})
            return True

        if scope['path'] != path:
            await send({
                'type': 'http.response.start', 'status': 404,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Not Found'})
            return True

        elif scope['method'] != method:
            await send({
                'type': 'http.response.start', 'status': 405,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Method Not Allowed'})
            return True

        return False

    async def authorize_request(
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

    async def sync_commands(self, commands: List[Any]) -> None:
        """Synchronize the commands with Discord."""
        for local in self.commands.values():
            found = [c for c in commands if c['name'] == local.name]
            if not found:
                await self.rest.create_global_command(local.to_dict())
                continue

            command = found[0]

            if (
                    (isinstance(local, SlashCommand) and local.description != command['description']) or
                    local.to_dict()['options'] != command.get('options', [])
            ):
                await self.rest.edit_global_command(command['id'], local.to_dict())
                continue

        for command in commands:
            if command['name'] not in self.commands:
                await self.rest.delete_global_command(command['id'])

    async def lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        event = await receive()
        if event['type'] == 'lifespan.startup':
            if self.register_commands:
                commands = await self.rest.fetch_global_commands()
                await self.sync_commands(commands)

            await send({'type': 'lifespan.startup.complete'})
        else:
            await send({'type': 'lifespan.shutdown.complete'})

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        if scope['type'] == 'lifespan':
            return await self.lifespan(scope, receive, send)

        if await self.verify_request(scope, send):
            return

        verified, body = await self.authorize_request(scope, receive)

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