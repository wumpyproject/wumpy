"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any

from ..rest import Requester

__all__ = ('Asset',)


class Asset:
    """Simple wrapper over a Discord CDN asset that can be read."""

    _rest: 'Requester'
    path: str

    __slots__ = ('_rest', 'path')

    BASE = 'https://cdn.discordapp.com'

    def __init__(self, rest: 'Requester', path: str) -> None:
        self._rest = rest

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

        return await self._rest.read_asset(self.url + f'.{fmt}', size=size)
