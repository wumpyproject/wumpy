from ..rest.requester import Requester, Route

__all__ = ('RESTClient',)


class RESTClient(Requester):
    """Requester subclass wrapping endpoints used for Discord applications."""

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs, headers={"Authorization": f"Bot {token}"})

    # Asset endpoint

    async def read_asset(self, url: str, *, size: int) -> bytes:
        return await self._bypass_request('GET', url, size=size)
