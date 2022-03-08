import json
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import anyio
from wumpy.rest import ApplicationCommandRequester, InteractionRequester

from .base import CommandInteraction, ComponentInteraction, InteractionType
from .commands import CommandRegistrar, SlashCommand
from .components.handler import ComponentHandler
from .utils import DiscordRequestVerifier

__all__ = ('InteractionAppRequester', 'InteractionApp')


class InteractionAppRequester(ApplicationCommandRequester, InteractionRequester):
    """Requester with endpoints used by InteractionApp."""

    __slots__ = ()


class InteractionApp(CommandRegistrar, ComponentHandler):
    """Simple interaction application implementing the ASGI protocol.

    This is a very bare implementation of the ASGI protocol that only does
    what's absolutely necessary for the Discord API.
    """

    api: InteractionAppRequester

    path: str

    def __init__(
        self,
        application_id: int,
        public_key: str,
        *,
        path: str = '/',
        token: Optional[str] = None,
        register_commands: bool = True,
    ) -> None:
        super().__init__()

        self.api = InteractionAppRequester(headers={'Authorization': f'Bot {token}'})
        self._verification = DiscordRequestVerifier(public_key)

        self.application_id = application_id
        self.register_commands = register_commands
        self.path = path

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
                    CommandInteraction(self, wrapped, self.api, data),
                    tg=tg
                )
            elif enum_val is InteractionType.message_component:
                self.handle_component(
                    ComponentInteraction(self, wrapped, self.api, data),
                    tg=tg
                )

            with anyio.fail_after(3):
                await complete.wait()

    async def _verify_request_target(
        self,
        scope: Dict[str, Any],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> bool:
        """Verify that the request was made to the correct endpoint.

        This method will respond to the request with an appropriate response
        if the request was made to the wrong endpoint.

        Returns:
            A boolean indicating whether the request was responded to. If it
            is `True` then the request has received a response and you should
            return immediately.
        """
        if scope['type'] != 'http':
            await send({
                'type': 'http.response.start', 'status': 501,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Not Implemented'})
            return True

        if scope['path'] != self.path:
            await send({
                'type': 'http.response.start', 'status': 404,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Not Found'})
            return True

        elif scope['method'] != 'POST':
            await send({
                'type': 'http.response.start', 'status': 405,
                'headers': [(b'content-type', b'text/plain')]
            })
            await send({'type': 'http.response.body', 'body': b'Method Not Allowed'})
            return True

        return False

    async def _authenticate_request(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]]
    ) -> Tuple[bool, Optional[bytes]]:
        """Authenticate the request and verify that it came from Discord.

        Returns:
            A two-item tuple. The first item is a boolean indicating whether
            the request could be authenticated and the second item is the body
            for the request, if it was received. It is not safe to assume that
            a body was received if the first item is `False`.
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

        verified = self._verification.verify(signature.decode('utf-8'), timestamp, body)

        return verified, body

    async def sync_commands(self, commands: List[Any]) -> None:
        """Synchronize the commands with Discord."""
        for local in self.commands.values():
            found = [c for c in commands if c['name'] == local.name]
            if not found:
                await self.api.create_global_command(self.application_id, local.to_dict())
                continue

            command = found[0]

            if (
                    (isinstance(local, SlashCommand) and local.description != command['description'])
                    or local.to_dict()['options'] != command.get('options', [])
            ):
                await self.api.edit_global_command(self.application_id, command['id'], local.to_dict())
                continue

        for command in commands:
            if command['name'] not in self.commands:
                await self.api.delete_global_command(self.application_id, command['id'])

    async def lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        event = await receive()
        if event['type'] == 'lifespan.startup':
            if self.register_commands:
                commands = await self.api.fetch_global_commands(self.application_id)
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

        if await self._verify_request_target(scope, send):
            return

        verified, body = await self._authenticate_request(scope, receive)

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
