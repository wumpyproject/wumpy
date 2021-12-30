from functools import partial
from typing import Any, Callable, Coroutine, Generator, Literal

import httpx
from typing_extensions import Self

from .utils import STATELESS

__all__ = ('Asset',)


class AssetData:
    """Awaitable and asynchronous iterator for asset data.

    The purpose of this class is to allow both iterating and awaiting to get
    the data from the asset. It is not use meant to be instantiated directly,
    use the `read()` method.
    """

    __slots__ = ('coro', '_aiter')

    def __init__(self, coro: Callable[[], Coroutine[Any, Any, httpx.Response]]) -> None:
        self.coro = coro
        self._aiter = None

    def __await__(self) -> Generator[Any, None, bytes]:
        return self.read().__await__()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> bytes:
        if self._aiter is None:
            resp = await self.coro()
            self._aiter = resp.aiter_bytes()

        return await self._aiter.__anext__()

    async def read(self) -> bytes:
        if self._aiter is not None:
            raise RuntimeError('Cannot await and iterate asset data at the same time')

        resp = await self.coro()
        return await resp.aread()


class Asset:
    """Simple wrapper over a Discord CDN asset that can be read.

    """

    path: str

    __slots__ = ('api', 'path')

    BASE = 'https://cdn.discordapp.com'

    def __init__(self, path: str, *, api=STATELESS) -> None:
        self.api = api
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

    def __aiter__(self) -> Self:
        return self

    @property
    def url(self) -> str:
        return self.BASE + self.path

    def read(
        self,
        *,
        fmt: Literal['jpeg', 'jpg', 'png', 'webp', 'gif', 'json'],
        size: int
    ) -> AssetData:
        """Read the content of this asset.

        Parameters:
            fmt: The format of the asset.
            size:
                The preferred size of the asset, has to be a power of two
                between 16 and 4096.

        Returns:
            A special awaitable and iterable object - depending on how you wish
            to receive the bytes.
        """
        if fmt not in {'jpeg', 'jpg', 'png', 'webp', 'gif', 'json'}:
            raise ValueError(
                "Image format must be one of: 'jpeg', 'jpg', 'png', 'webp', "
                "'gif, or 'json' for Lottie"
            )

        elif not (4096 >= size >= 16):
            raise ValueError('size argument must be between 16 and 4096.')

        elif size & (size - 1) != 0:
            # All powers of two only have one bit set: 1000
            # if we subtract 1, then (0111) AND it we should get 0 (0000).
            raise ValueError('size argument must be a power of two.')

        return AssetData(partial(self.api.read_asset, self.url + f'.{fmt}', size=size))
