from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..state import ApplicationState

__all__ = ('Asset',)


class Asset:
    """Simple wrapper over a Discord CDN asset that can be read."""

    _state: 'ApplicationState'
    path: str

    __slots__ = ('_state', 'path')

    BASE = 'https://cdn.discordapp.com'

    def __init__(self, state: 'ApplicationState', path: str) -> None:
        self._state = state

        self.path = path

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.path == self.path

    def __ne__(self, other: Any) -> bool:
        return not isinstance(other, self.__class__) or other.path != self.path

    def __hash__(self):
        return hash(self.path)

    def __repr__(self) -> str:
        return f'<Asset path={self.path}>'

    def __str__(self) -> str:
        return self.url

    @property
    def url(self) -> str:
        return self.BASE + self.path

    async def read(self, *, fmt: str, size: int) -> bytes:
        """Read the content of this asset."""
        if fmt not in {'jpeg', 'jpg', 'png', 'webp', 'gif', 'json'}:
            raise ValueError(
                "Image format must be one of: 'jpeg', 'jpg', 'png', 'webp', 'gif, or 'json' for Lottie"
            )

        elif not (4096 >= size >= 16):
            raise ValueError('size argument must be between 16 and 4096.')

        elif size & (size - 1) != 0:
            # All powers of two only have one bit set: 1000
            # if we subtract 1, then (0111) AND it we should get 0 (0000).
            raise ValueError('size argument must be a power of two.')

        return await self._state.http.read_asset(self.url + f'.{fmt}', size=size)
