import json
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from discord_typings import InteractionData
from wumpy.rest import ApplicationCommandRequester, InteractionRequester

from .commands import CommandRegistrar, command_payload
from .compat import ASGIRequest, Request
from .components.handler import ComponentHandler
from .models import CommandInteraction, ComponentInteraction
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

    async def _lifespan(
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
            return await self._lifespan(scope, receive, send)

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

        await self.handle_interaction(data, ASGIRequest(scope, receive, send))

    async def handle_interaction(self, data: InteractionData, request: Request) -> None:
        """Handle the interaction from the request by calling callbacks.

        This method returns once all callbacks have finished executing.

        Parameters:
            data: JSON serialized data received from the request.
            request:
                Class with a `respond()` method. There are two classes that
                implement this - one for ASGI applications and one for Sanic
                applications which are provided by the library.
        """
        if data['type'] == 2:
            await self.invoke_command(
                CommandInteraction.from_data(data, request)
            )
        elif data['type'] == 3:
            await self.invoke_component(
                ComponentInteraction.from_data(data, request),
            )

    async def sync_commands(self, commands: List[Any]) -> None:
        """Synchronize the commands with Discord."""
        await self.api.overwrite_global_commands(
            self.application_id, [command_payload(c) for c in commands]
        )
