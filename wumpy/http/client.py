from .requester import Requester, Route

__all__ = ('HTTPClient',)


class HTTPClient(Requester):
    """Requester subclass wrapping endpoints used for Discord applications."""

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs, headers={"Authorization": f"Bot {token}"})
