from typing import Optional
from urllib.parse import parse_qs, urlencode, urlsplit

import attrs
from typing_extensions import Literal, Self

from .._utils import get_api

__all__ = (
    'Asset',
)


@attrs.define(frozen=True)
class Asset:
    url: str

    BASE = 'https://cdn.discordapp.com'

    @classmethod
    def from_path(cls, path: str) -> Self:
        return cls(cls.BASE + path)

    def replace(
        self,
        *,
        fmt: Optional[Literal['jpeg', 'jpg', 'png', 'webp', 'gif', 'json']] = None,
        size: Optional[int] = None
    ) -> Self:
        url = urlsplit(self.url)
        path = url.path
        query = url.query

        if size is not None:
            if not (4096 >= size >= 16):
                raise ValueError('size argument must be between 16 and 4096.')

            elif size & (size - 1) != 0:
                # All powers of two only have one bit set: 1000
                # if we subtract 1, then (0111) AND it we should get 0 (0000).
                raise ValueError('size argument must be a power of two.')

            query = parse_qs(url.query)
            query['size'] = [str(size)]
            query = urlencode(query, doseq=True)

        if fmt is not None:
            if fmt not in {'jpeg', 'jpg', 'png', 'webp', 'gif', 'json'}:
                raise ValueError(
                    "Image format must be one of: 'jpeg', 'jpg', 'png', 'webp', "
                    "'gif, or 'json' (for Lottie)"
                )

            destination, _, _ = path.rpartition('.')
            path = f'{destination}.{fmt}'

        return self.__class__(f'{url.scheme}://{url.netloc}{path}?{query}')

    async def read(self) -> bytes:
        """Read the asset's content and return it as bytes."""
        return await get_api().read_asset(self.url)
