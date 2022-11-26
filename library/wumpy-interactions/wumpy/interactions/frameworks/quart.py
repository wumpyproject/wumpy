from functools import partial
from typing import Any, Optional, Dict, List, IO, Union

import anyio
from quart import current_app, json, request, jsonify, Response

from .._app import InteractionApp
from .._utils import race

__all__ = ('QuartInteractionApp',)


class QuartInteractionApp:
    """Compatability implementation for Quart.

    Examples:

        ```python
        from quart import Quart
        from wumpy.interactions.frameworks.quart import QuartInteractionApp

        # Import the InteractionApp instance with commands and components from
        # another file, this way the code is kept somewhat separate.
        from .interactions import app as interactions

        app = Quart(__name__)

        app.add_url_rule(
            '/interactions', QuartInteractionApp(interactions).handle_request,
            methods=['POST']
        )
        ```
    """

    def __init__(self, app: InteractionApp) -> None:
        self._app = app

    async def handle_request(self) -> Response:
        """Handle a request received from Quart.

        This method has to be called from a view function, or be setup as the
        view function for the url rule.

        Returns:
            The response to return to Quart. The underlying callback continues
            running as a background task.
        """
        signature: Optional[str] = None
        timestamp: Optional[bytes] = None

        for header, value in request.headers:
            lower = header.lower()

            if lower == 'content-type' and value.lower() != 'application/json':
                return Response('Unauthorized', 401, content_type='text/plain')

            if lower == 'x-signature-timestamp':
                timestamp = value.encode('utf-8')
            elif lower == b'x-signature-ed25519':
                signature = value

        if signature is None or timestamp is None:
            return Response('Unauthorized', 401, content_type='text/plain')

        body = await request.get_data()

        if not self._app.authenticate_request(signature, timestamp, body):
            return Response('Unauthorized', 401, content_type='text/plain')

        response: Optional[Response] = None
        responded = anyio.Event()

        async def respond_quart(
                data: Dict[str, Any],
                files: List[Union[IO[bytes], bytes]]
        ) -> None:
            nonlocal response

            if responded.is_set():
                raise RuntimeError(
                    'Cannot respond to interaction which has already received a response'
                )

            if not files:
                response = jsonify(data)
                responded.set()

        current_app.add_background_task(
            self._app.process_interaction, json.loads(body), respond_quart
        )

        await race(partial(anyio.sleep, 3), responded.wait)
        if response is not None:
            return response

        return Response('No content', 204, content_type='text/plain')
