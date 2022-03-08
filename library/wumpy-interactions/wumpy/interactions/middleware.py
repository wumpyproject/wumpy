from typing import TYPE_CHECKING, Any, Awaitable, Callable, Mapping, Optional

from .utils import DiscordRequestVerifier

if TYPE_CHECKING:
    from sanic.request import Request

try:
    from sanic.exceptions import Unauthorized  # type: ignore
    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False


__all__ = ('ASGIMiddleware',)


Receive = Callable[[], Awaitable[Mapping[str, Any]]]
Send = Callable[[Mapping[str, Any]], Awaitable[None]]

ASGIApp = Callable[[Mapping[str, Any], Receive, Send], Awaitable[None]]


class ASGIMiddleware:
    """ASGI-compliant middleware implementation that verifies interactions.

    It is up to whatever ASGI framework this is used with to ensure that the
    type, method and path is setup correctly - that is not checked for.

    Parameters:
        public_key:
            The public key from the Discord developer portal. This is used to
            verify the request according to Ed29915.
    """

    def __init__(self, app: ASGIApp, public_key: str) -> None:
        self.app = app

        self._verification = DiscordRequestVerifier(public_key)
        self._body = b''

    async def __call__(self, scope: Mapping[str, Any], receive: Receive, send: Send) -> None:
        signature: Optional[bytes] = None
        timestamp: Optional[bytes] = None

        for header, value in scope['headers']:
            if header.lower() == b'content-type' and value.lower() != b'application/json':
                await send({
                    'type': 'http.response.start', 'status': 415,
                    'headers': [(b'content-type', b'text/plain')],
                })
                await send({'type': 'http.response.body', 'body': b'Unsupported Media Type'})
                return

            if header.lower() == b'x-signature-timestamp':
                timestamp = value
            elif header.lower() == b'x-signature-ed25519':
                signature = value

        if signature is None or timestamp is None:
            await send({
                'type': 'http.response.start', 'status': 401,
                'headers': [(b'content-type', b'text/plain')],
            })
            await send({'type': 'http.response.body', 'body': b'Unauthorized'})
            return

        body = bytearray()
        request = {'more_body': True}  # Fake request to start the loop
        while request['more_body']:
            request = await receive()
            body.extend(request['body'])

        self._body = bytes(body)

        if not self._verification.verify(signature.decode('utf-8'), timestamp, self._body):
            await send({
                'type': 'http.response.start', 'status': 401,
                'headers': [(b'content-type', b'text/plain')],
            })
            await send({'type': 'http.response.body', 'body': b'Unauthorized'})
            return

        await self.app(scope, self._mimic_receive, send)

    async def _mimic_receive(self) -> Mapping[str, Any]:
        """Mimic a receive call from the ASGI server.

        Since we already consumed the body, we need to fake it for the coming
        middlewares and routes.

        Returns:
            A mimicked receive call, if called multiple times will continue
            returning an empty string.
        """
        body = self._body
        self._body = b''

        return {'type': 'http.request', 'body': body, 'more_body': False}


class SanicMiddleware:
    """Middleware implementation for Sanic.

    This middleware is not as easy to use as the `ASGIMiddleware`. Instead
    you'll need to instantiate this before hand, and await its `verify()`
    method.

    Examples:

        ```python
        verification = SanicMiddleware(...)  # Replace with your public key

        # It is recommended to attach this to a specific blueprint with the
        # route that interactions should go to.
        bp.on_request(verification.verify)
        ```

        ```python
        verification = SanicMiddleware(...)  # Replace with your public key

        # You can also use the functionality directly if you don't want to
        # create a blueprint for only the interactions endpoint.
        @app.route('/interactions')
        async def interactions_route(request):
            # Will raise a response if the request could not be verified.
            await verification.verify(request)

            ...  # The rest of your interactions logic
        ```

    Parameters:
        public_key:
            The public key from the Discord developer portal. This is used to
            verify the request according to Ed29915.
    """

    def __init__(self, public_key: str) -> None:
        if not SANIC_AVAILABLE:
            raise RuntimeError("Sanic has to be installed to use 'SanicMiddleware'")

        self._verification = DiscordRequestVerifier(public_key)

    async def verify(self, request: 'Request') -> None:
        """Verify that the Sanic request comes from Discord.

        Parameters:
            request: The request from Sanic to verify.

        Raises:
            Unauthorized: The request could not be verified.
        """
        signature = request.headers.get('X-Signature-Ed25519')
        timestamp = request.headers.get('X-Signature-Timestamp')

        if signature is None or timestamp is None:
            raise Unauthorized('Unauthorized')

        await request.receive_body()
        if not self._verification.verify(signature, timestamp.encode('utf-8'), request.body):
            raise Unauthorized('Unauthorized')
