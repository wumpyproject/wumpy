from typing import Any, Callable, Mapping, Awaitable, Optional

from .utils import DiscordRequestVerifier

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
        self._body = None
        self._sent = False

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
        """
        if self._sent:
            raise RuntimeError('Request body already received')

        self._sent = True
        return {'type': 'http.request', 'body': self._body, 'more_body': False}
