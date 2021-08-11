from ..http.client import HTTPClient
from .cache import Cache

__all__ = ('ApplicationState',)


class ApplicationState:
    """Central management for the whole library."""

    cache: Cache
    http: HTTPClient

    __slots__ = ('cache', 'http')

    def __init__(self, cache: Cache, http: HTTPClient) -> None:
        self.cache = cache
        self.http = http
